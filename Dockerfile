# syntax=docker/dockerfile:1
FROM python:3.13-slim AS build
WORKDIR /build
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir --prefix=/install ".[llm]"

FROM python:3.13-slim
LABEL org.opencontainers.image.title="intel-collection-eval" \
      org.opencontainers.image.description="Tests an AI agent on intelligence collection staff tasks and on resistance to elicitation." \
      org.opencontainers.image.source="https://classhuman.org"

# Run as an unprivileged user. Reports are written to /work/runs.
RUN useradd --create-home --uid 10001 ice
COPY --from=build /install /usr/local
WORKDIR /work
COPY bank ./bank
COPY examples ./examples
RUN mkdir runs && chown -R ice:ice /work
USER ice

ENV ICE_BANK=/work/bank \
    ICE_OUT=/work/runs \
    PYTHONUNBUFFERED=1

ENTRYPOINT ["ice"]
CMD ["--help"]
