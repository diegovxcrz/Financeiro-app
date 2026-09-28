import os
import re
import io
import traceback
import pandas as pd
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from ofxparse import OfxParser

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SENHA_PADRAO_PDF = "068906"

@app.get("/", response_class=HTMLResponse)
async def home():
    html_path = os.path.join(BASE_DIR, "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()

@app.post("/importar-banco")
async def importar_banco(
    file: UploadFile = File(...),
    senha: str = Form(default=SENHA_PADRAO_PDF)
):
    try:
        contents = await file.read()
        transacoes = []
        filename = file.filename.lower()

        senha_final = senha if senha else SENHA_PADRAO_PDF

        # 1. PROCESSAR OFX
        if filename.endswith('.ofx'):
            ofx = OfxParser.parse(io.BytesIO(contents))
            for t in ofx.account.statement.transactions:
                valor = float(t.amount)
                transacoes.append({
                    "data": t.date.strftime('%Y-%m-%d'),
                    "descricao": t.memo or t.payee or "Lançamento Banco",
                    "categoria": "Outros",
                    "tipo": "receita" if valor > 0 else "despesa",
                    "valor": abs(valor)
                })

        # 2. PROCESSAR CSV
        elif filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
            for _, row in df.iterrows():
                valor = float(str(row.get('Valor', 0)).replace(',', '.'))
                transacoes.append({
                    "data": str(row.get('Data', '')),
                    "descricao": str(row.get('Descrição', 'Lançamento CSV')),
                    "categoria": "Outros",
                    "tipo": "receita" if valor >= 0 else "despesa",
                    "valor": abs(valor)
                })

        # 3. PROCESSAR PDF
        elif filename.endswith('.pdf'):
            if not pdfplumber:
                return JSONResponse(
                    status_code=400,
                    content={"sucesso": False, "mensagem": "Instale a biblioteca pdfplumber: pip install pdfplumber"}
                )

            texto = ""
            try:
                with pdfplumber.open(io.BytesIO(contents), password=senha_final) as pdf:
                    for page in pdf.pages:
                        txt = page.extract_text()
                        if txt:
                            texto += txt + "\n"
            except Exception as pdf_err:
                if "password" in str(pdf_err).lower() or "PDFPasswordIncorrect" in str(pdf_err):
                    return JSONResponse(
                        status_code=400,
                        content={"sucesso": False, "mensagem": f"Palavra-passe incorreta para o PDF. A senha ({senha_final}) não abriu o arquivo."}
                    )
                raise pdf_err

            padrao = re.compile(r'(\d{2}/\d{2}(?:/\d{2,4})?)\s+(.*?)\s+(-?\s*R?\$\s*[\d\.,]+)')
            
            termos_ignorar = ["entradas:", "saídas:", "total", "resumo", "saldo anterior", "saldo final"]
            
            # Palavras na descrição que indicam que o lançamento é uma SAÍDA/DESPESA
            termos_saida = ["saida", "saída", "enviado", "pagamento", "compra", "debito", "débito", "tarifa", "transferência enviada", "pix enviado"]

            for linha in texto.split('\n'):
                if any(termo in linha.lower() for termo in termos_ignorar):
                    continue

                match = padrao.search(linha)
                if match:
                    data_raw, desc, valor_raw = match.groups()
                    desc_clean = desc.strip()
                    desc_lower = desc_clean.lower()

                    # Verifica se o número já veio com sinal negativo
                    tem_sinal_menos = '-' in valor_raw

                    v_str = valor_raw.replace('R$', '').replace('-', '').replace(' ', '').strip()

                    if '.' in v_str and ',' in v_str:
                        v_str = v_str.replace('.', '').replace(',', '.')
                    elif ',' in v_str:
                        v_str = v_str.replace(',', '.')

                    try:
                        valor_num = float(v_str)
                        if valor_num != 0:
                            # Se tiver sinal negativo OU se a descrição contiver palavras de saída, classifica como DESPESA
                            eh_despesa = tem_sinal_menos or any(t in desc_lower for t in termos_saida)

                            transacoes.append({
                                "data": data_raw,
                                "descricao": desc_clean,
                                "categoria": "Outros",
                                "tipo": "despesa" if eh_despesa else "receita",
                                "valor": abs(valor_num)
                            })
                    except ValueError:
                        continue

        return {"sucesso": True, "transacoes": transacoes}

    except Exception as e:
        print("ERRO DETALHADO:")
        traceback.print_exc()
        return JSONResponse(
            status_code=400,
            content={"sucesso": False, "mensagem": f"Erro no arquivo: {str(e)}"}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)