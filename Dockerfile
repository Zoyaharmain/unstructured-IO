FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DO_NOT_TRACK=true \
    UNSTRUCTURED_DISABLE_NOTICE=1 \
    HF_HOME=/opt/models \
    NUMBA_CACHE_DIR=/tmp/unstructured-numba \
    MPLCONFIGDIR=/tmp/unstructured-matplotlib \
    OMP_NUM_THREADS=2

RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 poppler-utils tesseract-ocr tesseract-ocr-eng libreoffice-writer \
    libgl1 libglib2.0-0 ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY local_api/requirements.txt local_api/constraints-tested.txt /app/local_api/
RUN python -m pip install 'torch==2.14.1+cpu' 'torchvision==0.29.1+cpu' \
      --index-url https://download.pytorch.org/whl/cpu \
    && python -m pip install -r local_api/requirements.txt -c local_api/constraints-tested.txt \
    && python -m pip check

COPY local_api/data/section_model.json /app/local_api/data/section_model.json
COPY scripts/warm_models.py /app/scripts/warm_models.py
ARG PRELOAD_HI_RES=true
RUN if [ "$PRELOAD_HI_RES" = "true" ]; then python scripts/warm_models.py --hi-res --sections; \
    else python scripts/warm_models.py --sections; fi

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin app \
    && chown -R app:app /opt/models
COPY local_api /app/local_api
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"
CMD ["python", "-m", "uvicorn", "local_api.app:app", "--host", "0.0.0.0", "--port", "8000"]
