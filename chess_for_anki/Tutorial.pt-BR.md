# ♟️ Chess for Anki · Sua primeira partida

Cada cartão treina uma sequência de xadrez, chamada **linha**. Você joga com uma cor, e o tabuleiro responde pela outra. Na Abertura Italiana, por exemplo, você pode praticar o desenvolvimento do bispo e dos cavalos até conseguir lembrar da sequência sem ajuda.

## 1. Abra o tabuleiro

1. Se o menu **♟️ Chess for Anki** já aparece no topo do Anki, siga para o próximo passo. Para uma primeira instalação no computador, abra **Tools → Add-ons → Install from file…**, selecione o arquivo `.ankiaddon` e reinicie o Anki.
2. A instalação começa sem cards ou baralho de xadrez. Na tela inicial, clique em **Baixar deck inicial gratuito (.apkg)** ou **Download free starter deck (.apkg)**, baixe **Chess-for-Anki-Foundations.apkg**, com 30 cartões, e importe pelo menu **Arquivo → Importar** do Anki. O antigo **Chess-for-Anki-Starter.apkg**, com 60 cartões, continua gratuito como download separado nas [versões da comunidade](https://github.com/fernandomec/chess-for-anki-community/releases/tag/v1.4.2-preview). Para montar seu próprio material, escolha **Create my own cards**.
3. Abra **Chess → 01 - Foundations → 01 - Openings → White** e clique em **Study Now** para praticar com as brancas. Para treinar as pretas, abra **Black**. Na tela do cartão, **Play as White** ou **Play as Black** indica a sua cor.

## 2. Jogue uma linha com as brancas

Se **Demo on first view** estiver marcada, a primeira exibição começa na posição inicial. Clique em **Next move** para ver um único lance das brancas ou das pretas. **Previous move** retrocede um lance e restaura o tabuleiro e a explicação da posição anterior. A última posição fica na tela até você clicar em **Start practice**. Durante a tentativa, **Show demo** permite rever a linha desde o início. **Resume practice** devolve o tabuleiro à posição em que você estava respondendo.

**Onde configurar.** Na tela de boas-vindas e no primeiro cartão, clique em **Abrir configurações** (ou **Open settings**). Depois, use o menu superior **♟️ Chess for Anki → Settings**. Ali você pode mudar o nível, a demonstração inicial e o som das peças. A opção **Confetti on completion** liga ou desliga os confetes. A mensagem **Congratulations!** aparece ao completar a rodada corretamente.

No cartão **Italian - central break · White** do Foundations, experimente estes lances. As letras na borda do tabuleiro indicam as colunas e os números indicam as fileiras. Arraste a peça ou clique primeiro na casa de origem e depois na de destino.

| Sua vez | O que fazer | Resposta automática |
| --- | --- | --- |
| 1. e4 | Mova o peão de **e2** para **e4**. | O peão preto vai de **e7** para **e5**. |
| 2. Nf3 | Mova o cavalo de **g1** para **f3**. | O cavalo preto vai de **b8** para **c6**. |
| 3. Bc4 | Mova o bispo de **f1** para **c4**. | O bispo preto vai de **f8** para **c5**. |
| 4. c3 | Mova o peão de **c2** para **c3**. | As pretas jogam **Nf6**. A rodada **Noobie** termina. |

Em outra abertura, a resposta esperada pode ser diferente. O cartão segue a linha gravada. Se você jogar uma alternativa, pode ouvir **“Try a knight”** (“tente um cavalo”), por exemplo. Tente de novo na mesma posição quantas vezes precisar. **Voice on/off** liga ou desliga a narração em inglês. Escolha a velocidade em **Voice speed**, ao lado desse botão, ou em **Settings → Narration speed**. As opções vão de 0,5× a 2×, com 1,5× como padrão. A escolha fica salva neste computador e vale para os anúncios, dicas e explicações. Para ligar ou desligar o som das peças, use **Settings → Piece sounds**.

## 3. Decida quando repetir

- **Restart** volta ao início da tentativa no mesmo cartão. Use quando quiser praticar de novo agora.
- **End round** encerra a tentativa e abre a resposta. Se esqueceu a continuação, clique em **Repeat later** no verso. Isso registra **Again** e o Anki agenda outra tentativa de acordo com seu baralho.
- No verso, use **← / →** ou clique em um lance da notação para rever a posição. As notas em **Idea behind the line**, quando presentes, explicam o plano da sequência.
- Ao avaliar, escolha **Again** se esqueceu, **Hard** se lembrou com dificuldade, **Good** se lembrou normalmente ou **Easy** se foi fácil.

## 4. Entenda os níveis

### Por que jogar esse lance?

Durante a demonstração, cada clique em **Next move** mostra o objetivo do lance e sua relação com o plano da linha. As explicações em inglês cobrem as 34 sequências distintas da coleção, incluindo as partidas clássicas e os mates.

O padrão é **System voice**, a síntese de voz disponível no dispositivo. Para usar a voz natural Michael, baixe **English-Michael-Voice-Pack.zip**, importe em **♟️ Chess for Anki → Language packs** e selecione a voz. O mesmo menu permite escolher separadamente o texto e a narração. Os idiomas básicos dependem das vozes instaladas no sistema; as gravações naturais dos outros idiomas ainda serão produzidas e revisadas.

### Envie um relato de erro

Abra **Feedback / Report an issue**, escreva o assunto e descreva o problema. Você pode anexar uma imagem PNG, JPEG ou WebP e conferir a prévia. O formulário converte a imagem para PNG e não gera arquivos ZIP.

Clique em **Review and submit on GitHub**. O navegador abre o relato com o texto preparado; o print fica copiado para colar no editor com Ctrl+V. Revise e envie pelo GitHub. Para textos muito longos, cole primeiro o texto copiado e depois use **Copy screenshot** para colar a imagem. **View reported issues** abre os relatos para leitura e visualização das imagens na própria página. Para publicar o relato, é necessário entrar em uma conta do GitHub. Os relatos são públicos.

O autor acompanha os relatos pela aba **Issues**. Avisos no GitHub ou por e-mail dependem das preferências de notificações da conta e de **Watch** no repositório. As validações de imagem e texto reduzem riscos, mas não são antivírus nem uma garantia absoluta sobre arquivos enviados diretamente ao GitHub.

| Nível | Até onde você joga |
| --- | --- |
| Noobie | 4 lances por cor |
| Beginner | 8 lances por cor |
| Intermediate | 12 lances por cor |
| Advanced | 20 lances por cor |
| HACKER | Toda a linha gravada |

O nível escolhido vale para os próximos cartões. Para subir automaticamente, complete **três sequências diferentes** na profundidade do nível atual, sem consultar lances ou usar dicas, e avalie cada uma com **Good** ou **Easy**. Ao revelar um lance com **Next move**, a tentativa conta como assistida. Você pode abrir a demonstração e sair antes do primeiro lance para continuar de memória.

Uma linha curta termina no último lance disponível. Para contar para a promoção, ela precisa ter lances suficientes para o nível. Exercícios de mate com posição inicial personalizada treinam a solução inteira e ficam fora dessa contagem.

## 5. Crie um cartão seu

1. Abra **♟️ Chess for Anki → Create cards / Import PGN**. Em **Add to Deck**, escolha o baralho. Em **Title**, escreva **Italiana - desenvolvimento das brancas**.
2. Em **I am playing as…**, marque **White**. Em **Starting Position**, deixe **Opening** para começar com as peças nas casas iniciais.
3. Cole a linha abaixo em **Moveset PGN**. PGN é o formato de texto que registra os lances de uma partida. Na notação em inglês, **N** indica cavalo e **B** indica bispo.

   `1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. Nc3 Nf6`

4. Clique em **Add**. Abra o baralho escolhido para jogar o cartão. Para montar a sequência no tabuleiro, use **Manual Input**, jogue os lances de ambos os lados e confirme com **Set** antes de clicar em **Add**. Para carregar um arquivo `.pgn`, use **Import** na seção **Moveset PGN**.

**Para criar um exercício de mate**, escolha **Custom → Manual Edit** em **Starting Position**, monte a posição e confirme com **Set**. Depois insira os lances da solução em **Moveset PGN**. Também é possível colar uma posição em formato FEN, que descreve onde as peças estão e de quem é a vez.
