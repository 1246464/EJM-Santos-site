# Roadmap do aplicativo nativo EJM Santos

O objetivo é lançar uma loja de mel simples, confiável e rápida de usar. A ordem
abaixo evita depender de funções de marketplace que não ajudam a primeira venda.

## Etapa 1 — Pedido completo com pagamento no recebimento

Status: **implementada no código; aguardando validação em aparelho e publicação da API**.

- [x] Escolher um endereço salvo.
- [x] Recalcular preços e validar estoque no servidor.
- [x] Calcular distância, frete, subtotal e total.
- [x] Criar o pedido e seus itens em uma transação.
- [x] Evitar pedido duplicado em reenvios da mesma compra.
- [x] Dar baixa no estoque sem permitir valor negativo.
- [x] Exibir confirmação e limpar o carrinho.
- [x] Cobrir preço, estoque e idempotência com testes automatizados.
- [ ] Testar o fluxo visual em emulador e aparelho Android.
- [ ] Publicar a nova versão do backend antes de distribuir o APK.

Critério de conclusão: um cliente consegue montar o carrinho, escolher o endereço,
confirmar um pedido e encontrá-lo no histórico.

## Etapa 2 — Pagamento digital real

Status: **integração Stripe implementada, mas pausada para ser concluída por último; aguardando credenciais, webhook e teste no modo sandbox**.

- [x] Escolher o Stripe como provedor de cartão.
- [x] Criar intenção de pagamento exclusivamente no servidor.
- [x] Integrar o Stripe PaymentSheet nativo.
- [x] Validar a assinatura do webhook.
- [x] Tornar o webhook a fonte do estado `paid`/`failed`.
- [x] Devolver estoque quando um PaymentIntent é cancelado, sem duplicar a devolução.
- [ ] Cadastrar as chaves e o webhook no ambiente de produção.
- [ ] Validar cartão aprovado, recusado e autenticação 3DS no modo de teste.
- [ ] Definir expiração automática para pedidos abandonados.
- [ ] Habilitar Pix quando estiver disponível/configurado na conta Stripe.
- [ ] Implementar reembolso e cancelamento administrativo.

Critério de conclusão: nenhum dado bruto de cartão passa pelo backend da EJM Santos,
e o pedido só aparece como pago após confirmação autenticada do provedor.

## Etapa 3 — Conta, segurança e privacidade

Status: **controles essenciais implementados; aguardando verificação de e-mail e documentos públicos**.

- [x] Armazenar o token com criptografia apoiada pelo Android Keystore.
- [x] Criar renovação e revogação de tokens.
- [x] Adicionar recuperação de senha por código com expiração e limite de tentativas.
- [x] Permitir alteração de senha dentro do aplicativo.
- [ ] Adicionar verificação de e-mail.
- [x] Limitar tentativas de login, cadastro e renovação de sessão.
- [x] Permitir exclusão e anonimização segura da conta, preservando pedidos operacionais.
- [ ] Publicar política de privacidade e termos de compra.

Critério de conclusão: sessões podem ser encerradas pelo servidor e o cliente possui
os controles básicos sobre sua conta e seus dados.

## Etapa 4 — Operação e pós-venda

Status: **experiência inicial implementada; notificações push e regras operacionais ainda pendentes**.

- [x] Enviar confirmação e mudanças de status por e-mail.
- [ ] Adicionar notificações push no Android.
- [x] Exibir acompanhamento da entrega em uma linha do tempo nativa.
- [x] Adicionar contato rápido com o atendimento, vinculado ao número do pedido.
- [x] Permitir comprar novamente a partir do histórico com preço e estoque atualizados.
- [ ] Definir regras de entrega, cancelamento, troca e estoque.
- [ ] Configurar monitoramento de erros e rotina de restauração de backup.

Critério de conclusão: a equipe consegue receber, separar, entregar, cancelar e
acompanhar pedidos sem depender de alterações manuais no banco.

## Etapa 5 — Conversão e publicação

- [ ] Completar origem, peso, lote, validade e conservação dos produtos.
- [ ] Adicionar cupons, favoritos sincronizados e frete grátis configurável.
- [ ] Melhorar acessibilidade, estados offline e desempenho.
- [ ] Criar testes instrumentados para os fluxos críticos.
- [ ] Gerar AAB assinado, ícones finais, capturas e ficha da Play Store.
- [ ] Executar um beta fechado antes da publicação geral.

Critério de conclusão: versão assinada, testada com clientes reais e acompanhada por
monitoramento de falhas e métricas essenciais de compra.
