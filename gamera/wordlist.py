"""Lista de palavras em português (sem acentos) para frases-senha.

Palavras curtas e fáceis de digitar. Quanto maior a lista, mais entropia por
palavra: cada palavra vale log2(len(WORDS)) bits.
"""

_RAW = """
abacate abelha abismo abrigo acampar aceno acervo adega afeto agenda agulha
alavanca alce alecrim alface alga algodao alicate alma almoco altar alvo
amarelo ameixa amigo amora ancora andorinha anel angulo animal antena anzol
apito aquario arame arara arco areia argola armario arroz artista asfalto
astro atalho atleta aurora avental aveia aviao azeite azul bacia bagagem
baleia balde balao bambu banana banco bandeira banho barco barril barro
batata bateria baleeiro beija bengala berco besouro bicicleta bigode bilhete
biscoito bispo bloco boca bolacha bolha bolo bolsa bombeiro boneca borboleta
bosque bota botao brasa brinco brisa broto bruxa bucha bule buraco bussola
cabana cabelo cabra cacau cachorro caderno cadeira caixa cajado caju calor
cama camelo caminho camisa campo canela caneta canoa cantor capim capivara
caqui caracol carga carimbo carneiro carro carta casaco casca castelo
castanha cavalo caverna cebola cedro cegonha cenoura cereja cesto chave
chaleira chapeu charco chuva cidade cigarra cinema cinto circo cisne clima
cobra coelho cofre coisa colar colher colina cometa concha conto copo coral
corda coruja costa couve cratera cravo crepe cristal cubo cuia cume cupim
dado dama danca dardo dedal degrau dente deserto desenho diamante disco
doce domino dragao duna eco eixo elefante elmo embrulho enxada envelope
escada escova escudo esfera espelho espiga esponja estrela estufa faca
fada farol farofa fazenda feijao feira ferro festa figo fita flauta flecha
floresta foca fogo foguete folha fonte forno fruta fumaca funil furacao
gaivota galho galo gamela ganso garfo garrafa gato gaveta geada geleia
gelo girafa girassol globo goiaba gol golfinho gorro gota grade grama
granito grilo gruta guarda guitarra harpa helice hiena horta hotel iate
igreja ilha ima inseto inverno ipe janela jardim jarra javali jegue jiboia
joaninha joia jornal jupiter lago lagoa lagosta lama lampada lanche lapis
laranja lareira lata leao leite lenco lenha lente leque letra limao linha
livro lobo locomotiva lontra lousa lua lupa luva madeira maca macaco
machado madrugada magia malha mamute manga manta mapa mar marfim mariposa
martelo mascara massa mato medalha mel melancia menta mesa meteoro milho
mina mochila moeda moinho mola montanha morango mosaico mosca motor mula
museu musgo nabo navio neblina neve ninho noite nota novelo nuvem oceano
oculos oficina olho onda onibus orvalho osso ostra ouro ovelha ovo paca
padaria palha palmeira panela pantano papel papagaio parafuso parede pato
pavao pedra peixe pena peneira pepino pera perfume pernil peteca piano
picole pijama pilha pimenta pincel pinguim pinha pipa pipoca pirata piscina
planeta pluma pneu poeira polvo pomar ponte porta potro pote praia prato
prego presente prisma pudim pulseira quadro queijo quiabo raio raiz rampa
raposa rato rede regua relogio remo rena rio robo rocha roda rolha rosa
rubi rua sabao sabia saco saguao sal salsa sapato sapo satelite selva
semente serra sereia seta silencio sino sofa sol soldado sombra sopa
sorvete suco tambor tamanco tapete tartaruga tatu teatro teclado telhado
tempo tenis terra tesoura tigre tijolo tinta tomate topazio torre touro
trator trem trevo trigo trombone trono tucano tulipa tunel uva vaca vagao
vale varal vaso veleiro vela veludo vento verao vespa vidro vila vinho
violao violino vulcao xadrez xale zebra zinco
alegre amplo antigo astuto audaz bravo breve brilhante calmo claro curioso
doce eterno exato feliz fiel firme forte gentil grande habil honesto
humilde imenso jovem justo largo leal leve limpo livre lindo longo macio
manso nobre novo nublado otimo pacato perfeito pleno pronto quente rapido
raro real rico robusto sabio sereno serio simples sincero solido suave
sutil tenaz tranquilo unico valente veloz vivo
abrir achar andar aprender brincar cantar correr dancar desenhar dormir
escrever estudar falar ganhar girar guardar ler mergulhar nadar navegar
olhar pensar plantar pular remar rir saltar seguir sonhar subir sorrir
tocar trocar viajar voar
"""

WORDS: tuple[str, ...] = tuple(sorted(set(_RAW.split())))
