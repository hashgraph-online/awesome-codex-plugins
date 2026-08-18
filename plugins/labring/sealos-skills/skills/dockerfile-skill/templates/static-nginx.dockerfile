FROM nginxinc/nginx-unprivileged:1.31.3-alpine3.24

COPY --chown=101:101 . /usr/share/nginx/html

USER 101:101

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
