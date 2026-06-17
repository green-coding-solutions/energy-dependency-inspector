# Tool Comparison

How does the dependency-resolver compare to other tools with similar purposes?

## Examples

### gmt-unicorn

In the subfolder [gmt-unicorn](./gmt-gunicorn/) you can find the results of different tools targetting the Docker container "green-coding-gunicorn-container".

**Syft:**

```sh
# syft-json
syft $(docker container inspect -f "{{.Image}}" green-coding-gunicorn-container) -o syft-json > docs/tool-comparison/gmt-gunicorn/syft-json.json

# spdx-json
syft $(docker container inspect -f "{{.Image}}" green-coding-gunicorn-container) -o spdx-json > docs/tool-comparison/gmt-gunicorn/syft-spdx_json.json

# github-json
syft $(docker container inspect -f "{{.Image}}" green-coding-gunicorn-container) -o github-json > docs/tool-comparison/gmt-gunicorn/syft-github_json.json

# Using custom template
syft $(docker container inspect -f "{{.Image}}" green-coding-gunicorn-container) -o template -t docs/tool-comparison/syft-custom-template.tmpl > docs/tool-comparison/gmt-gunicorn/syft-custom.json
```

**Trivy:**

```sh
# native
trivy image --format spdx-json --output docs/tool-comparison/gmt-gunicorn/trivy-spdx_json.json $(docker container inspect -f "{{.Image}}" green-coding-gunicorn-container)

# docker run
docker run --rm -v trivy-cache:/root/.cache/ -v /var/run/docker.sock:/var/run/docker.sock -v $PWD:/opt/app aquasec/trivy:latest image --format spdx-json --output /opt/app/docs/tool-comparison/gmt-gunicorn/trivy-spdx_json.json $(docker container inspect -f "{{.Image}}" green-coding-gunicorn-container)
```

### kadai-rest-spring-example-boot

See repo: <https://gitlab.com/envite-consulting/sustainable-software-architecture/kadai/kadai-resource-efficiency/-/tree/main/kadai-rest-spring-example-boot>

Outputs are placed in sub-folder [kadai](./kadai/).

**Syft:**

```sh
# syft-json
syft registry.gitlab.com/envite-consulting/sustainable-software-architecture/kadai/kadai-example-spring-boot:kadai-10.1.0 -o syft-json > docs/tool-comparison/kadai/syft-json.json
```
