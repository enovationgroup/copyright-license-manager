FROM python:3.11-slim-bookworm AS install

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gnupg \
    jq \
    tar \
    gzip \
    unzip \
 && rm -rf /var/lib/apt/lists/*

FROM install AS glab

# Use TARGETARCH for multi-arch support
ARG TARGETARCH

# Install GitLab CLI based on architecture
RUN GLAB_VERSION=$(curl -s https://gitlab.com/api/v4/projects/34675721/repository/tags \
      | jq -r '.[0].name' \
      | sed 's/^v//') && \
    echo "Installing glab version ${GLAB_VERSION} for architecture ${TARGETARCH}" && \
    curl -sSL "https://gitlab.com/gitlab-org/cli/-/releases/v${GLAB_VERSION}/downloads/glab_${GLAB_VERSION}_linux_${TARGETARCH}.tar.gz" \
      | tar -xz -C /usr/local bin/glab

RUN glab --version

# Install GitHub CLI
FROM install AS gh

# Use TARGETARCH for multi-arch support
ARG TARGETARCH

# Fetch and install latest GitHub CLI
RUN GH_VERSION=$(curl -s https://api.github.com/repos/cli/cli/releases/latest \
      | grep '"tag_name":' \
      | cut -d '"' -f 4 | sed 's/^v//') && \
    echo "Installing gh version $GH_VERSION for architecture ${TARGETARCH}" && \
    curl -sSL "https://github.com/cli/cli/releases/download/v${GH_VERSION}/gh_${GH_VERSION}_linux_${TARGETARCH}.tar.gz" \
    | tar -xz --strip-components=1 -C /usr/local gh_${GH_VERSION}_linux_${TARGETARCH}/bin/gh

# Check install
RUN gh --version

FROM python:3.11-slim-bookworm AS runtime

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        gnupg \
        jq && \
    rm -rf /var/lib/apt/lists/*

COPY --from=glab /usr/local/bin/glab /usr/bin/glab
COPY --from=gh /usr/local/bin/gh /usr/bin/gh

RUN mkdir -p /app /work

COPY . /app

WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt; \
    pip install --no-cache-dir -e .

WORKDIR /work

ENTRYPOINT [ "clmgr" ]
