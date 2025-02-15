FROM python:3.11-slim-bookworm

COPY requirements.txt /

RUN \
  python3 -m pip install -r requirements.txt && rm -rf ~/.cache && rm requirements.txt

ADD /ex_app/cs[s] /ex_app/css
ADD /ex_app/im[g] /ex_app/img
ADD /ex_app/j[s] /ex_app/js
ADD /ex_app/l10[n] /ex_app/l10n
ADD /ex_app/li[b] /ex_app/lib

COPY --chmod=775 healthcheck.sh /

# Copy entrypoint script into the container
COPY --chmod=775 ex_app/lib/entrypoint.sh /ex_app/lib/

WORKDIR /ex_app/lib

#ENTRYPOINT ["./entrypoint.sh"]
HEALTHCHECK --interval=2s --timeout=2s --retries=300 CMD /healthcheck.sh
