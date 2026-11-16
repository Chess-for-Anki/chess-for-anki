# Chess for Anki: comece a praticar

Cada cartão treina uma sequência salva. Você joga com uma cor; o adversário responde com os próximos lances dessa linha. O objetivo é entender e lembrar a continuação.

## Instalação e amostra gratuita

A **prévia 1.6.0** e seu pacote estão disponíveis na [release da prévia](https://github.com/Chess-for-Anki/chess-for-anki/releases/tag/v1.6.0-preview).

1. No Anki desktop, abra **Tools > Add-ons > Install from file**, selecione o `.ankiaddon` e reinicie.
2. Na tela inicial, escolha **Baixar deck inicial gratuito (.apkg)** ou **Download free starter deck (.apkg)**.
3. Importe **Chess-for-Anki-Free-Sample.apkg** em **Arquivo > Importar** e abra **Chess - Free Sample**.

Instalar o add-on não cria cartões nem instala gravações naturais.

A amostra tem **22 cartões**: cinco aberturas para brancas e pretas (10), três Brilliancy, três finais, três meios-jogos e três táticas. As aberturas são Italiana, Gambito da Dama Recusado, Escocesa, Sistema Londres e Defesa Siciliana.

As linhas chegam a uma transição útil para o meio-jogo. Não existe um lance universal que encerre toda abertura. São exemplos de estudo, sem prometer repertório completo ou respostas forçadas. Foundations e Starter continuam como [downloads gratuitos anteriores](https://github.com/Chess-for-Anki/chess-for-anki/tree/downloads/decks).

## Veja, entenda e tente

Use **Next move** e **Previous move** para avançar e voltar na demonstração. Leia a explicação: o que mudou no centro, no desenvolvimento ou na segurança dos reis?

Escolha **Start practice**. Arraste a peça ou clique na origem e no destino. Depois do lance correto, o adversário executa a resposta salva. Uma alternativa legal pode ser boa e ainda ser diferente da linha estudada.

- **Show demo:** reveja a explicação.
- **Resume practice:** retorne à tentativa.
- **Restart:** tente de novo agora.
- **End round:** encerre a tentativa e veja a resposta.
- **Repeat later:** registre Again para revisar depois.

Consultar demonstração ou dica torna a tentativa assistida. Avalie sua lembrança independente: Again se esqueceu, Hard se lembrou com dificuldade, Good se lembrou normalmente e Easy se foi imediato.

## Posição inicial e último lance

Nos exercícios personalizados, o destaque mostra o lance do adversário anterior à solução. **Previous move** identifica contexto registrado ou fornecido pelo autor. **Setup move** identifica preparação legal construída, sem afirmar que aconteceu numa partida.

Esse lance não aumenta o tamanho da solução. Os cartões já importados e seu histórico continuam preservados.

## Crie material próprio

Criação e importação de PGN continuam no núcleo gratuito. Abra **Create cards / Import PGN**, escolha baralho, título e cor. Para começar da posição normal, use **Opening** e informe a linha em **Moveset PGN**, ou monte os lances em **Manual Input**.

Para um exercício personalizado:

1. Escolha a cor treinada e selecione **Custom**.
2. Cole em **Starting Position PGN/FEN** um PGN de preparação que termine após o lance do adversário, antes da solução. A posição e o contexto são preenchidos automaticamente.
3. Para FEN ou **Manual Edit**, informe também a FEN anterior completa e o lance em coordenadas, como `e7e5`. Marque **Constructed setup move** quando for preparação construída.
4. Escreva a solução separadamente em **Moveset PGN** e clique em **Add**.

Novos exercícios personalizados exigem contexto válido. Uma FEN isolada não revela o lance anterior. Mudar cor ou posição pode apagar contexto incompatível. Compartilhe somente material que você tem direito de distribuir.

## Níveis, efeitos e voz

As aberturas usam profundidades de 4, 8, 12, 20 ou todos os lances salvos por lado. Linhas curtas terminam no seu fim real; exercícios personalizados usam a solução inteira. Três linhas diferentes, suficientemente longas, concluídas sem ajuda e avaliadas Good ou Easy promovem o nível.

O halo turquesa e o indicador `!!` destacam um lance selecionado para ensino. Não avaliam automaticamente todos os lances. Em **Settings**, desligue separadamente destaque, partículas ou som. O som também respeita **Piece sounds**. Há controles de velocidade, demonstração e confetes.

A fala básica depende de uma voz instalada no dispositivo. A [voz natural inglesa Michael](https://github.com/Chess-for-Anki/chess-for-anki/releases/download/v1.4.2-preview/English-Michael-Voice-Pack.zip) é opcional e importada em **Language packs**. Frases sem gravação podem usar a voz do sistema. Outros idiomas naturais estão planejados; Hindi ainda precisa de suporte no add-on.

## Ajuda e disponibilidade

[Comunidade oficial](https://github.com/Chess-for-Anki/chess-for-anki) · [Relatar um problema](https://github.com/Chess-for-Anki/chess-for-anki/issues) · [Apoiar o projeto](https://github.com/Chess-for-Anki/chess-for-anki/blob/downloads/SUPPORT.md)

Pacotes ampliados e PRO estão em preparação, sem checkout ativo. O núcleo gratuito, os materiais já distribuídos e o estudo offline dos cartões importados permanecem disponíveis.

Windows com Anki desktop 26.9.4 é o ambiente testado; esta prévia passou por verificações isoladas de coleção, importação e tabuleiro. A compatibilidade com macOS, Linux e mobile não foi estabelecida. O código e os créditos acompanham a distribuição sob AGPL-3.0.
