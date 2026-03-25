# Jupyter Notebooks (ad-hoc solutions)

- [Extract raw PNG images from PDF Files and pack them into separate zip files](Extract_Images_(PNGs)_from_PDF.ipynb) 
  (see it at [JN Viewer](https://nbviewer.jupyter.org/github/fmbento/Jupyter-Notebooks_ad-hoc-solutions/blob/main/Extract_Images_%28PNGs%29_from_PDF.ipynb); run it on [Binder](https://mybinder.org/v2/gh/fmbento/Jupyter-Notebooks_ad-hoc-solutions/master?filepath=Extract_Images_(PNGs)_from_PDF.ipynb) or on [Google Colab](https://colab.research.google.com/github/fmbento/Jupyter-Notebooks_ad-hoc-solutions/blob/master/Extract_Images_(PNGs)_from_PDF.ipynb))
  
- [Extract Labels from HMD Filenames (for Universal Viewer)](TomHarper_HMD_Labels_from_Filenames.ipynb)
(see it at [JN Viewer](https://nbviewer.jupyter.org/github/fmbento/Jupyter-Notebooks_ad-hoc-solutions/blob/main/TomHarper_HMD_Labels_from_Filenames.ipynb); run it on [Binder](https://mybinder.org/v2/gh/fmbento/Jupyter-Notebooks_ad-hoc-solutions/master?filepath=TomHarper_HMD_Labels_from_Filenames.ipynb) or on [Google Colab](https://colab.research.google.com/github/fmbento/Jupyter-Notebooks_ad-hoc-solutions/blob/master/TomHarper_HMD_Labels_from_Filenames.ipynb))


[Google Colab: Datasets_faz_sample_de_10_50_100_500_ou_1000_registos.ipynb](https://colab.research.google.com/github/fmbento/Jupyter-Notebooks_ad-hoc-solutions/blob/main/Datasets_faz_sample_de_10_50_100_500_ou_1000_registos.ipynb)

[Google Colab: Datasets_Sample_Maker_10_50_100_500_or_1K_records.ipynb](https://colab.research.google.com/github/fmbento/Jupyter-Notebooks_ad-hoc-solutions/blob/main/Datasets_Sample_Maker_10_50_100_500_or_1K_records.ipynb)

----
----
# Python CLI Scripts

## [reverse-proxy-iaedu-openai](https://github.com/fmbento/Jupyter-Notebooks_ad-hoc-solutions/blob/main/reverse-proxy-iaedu-openai.py).py

**IAedu.pt → OpenAI Proxy**

Proxy leve e robusto que permite usar aAPI da **iaedu.pt** como se fosse um modelo OpenAI nativo /compatível (/v1/chat/completions).
Especialmente otimizado para funcionar com o Flowise (incluindo Condition Agent), LangChain, n8n e outras ferramentas.

### Funcionalidades
·        Converte o _endpoint_ de streaming da iaedu.pt para o formato OpenAI

·        Suporte completo a respostas em stream (para chat visual)

·        Modo não-stream com resiliência forte para Condition Agent do Flowise

·        Envio correto do campo obrigatório user\_info

·        Fallback inteligente quando a iaedu devolve texto puro em vez de JSON

·        Health check simples

·        Totalmente assíncrono com httpx

### Configuração

Edite as variáveis no início do ficheiro.

_Dica: Pode sobrescrever o user\_info dinamicamente enviando-o no campo user\_info ou metadata.user\_info da requestOpenAI._

### Instalação e Execução

#### Instalar dependências

_pip install fastapi uvicorn httpx_

#### Executar o servidor

_uvicorn main:app --host 0.0.0.0 --port 8008 --reload_

#### Em produção (recomendado)

_uvicorn main:app --host 0.0.0.0 --port 8008 --workers4_

#### Como usar no Flowise ou qualquer outra ferramenta

_[http://SEU\_IP\_OU\_DOMINIO:8008/v1](http://SEU_IP_OU_DOMINIO:8008/v1)_

##### Modelo:

_gpt-4o-mini_

Nota: o proxy aceita tanto stream: true como stream: false.

### Endpoints disponíveis

POST /v1/chat/completions → Principal (streaming e non-streaming)

GET /v1 → Health check

### Notas importantes
·        Ocampo user\_info **deve** ser enviado como string JSON (o proxy tratadisso automaticamente).

·        Emmodo non-stream, o proxy força um JSON de saída quando necessário para evitarque os nós Condition Agent do Flowise quebrem.

·        Recomenda-serodar o proxy em Docker ou com systemd/PM2 em ambiente de produção.

·        Recomenda-seusar em ambiente Docker ou com PM2 / systemd em produção

Feito com ❤️ para integrar iaedu.pt com Flowise, n8n, etc..
