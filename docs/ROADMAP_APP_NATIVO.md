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

Status: **planejada; depende da escolha e das credenciais do gateway**.

- [ ] Escolher Stripe, Mercado Pago ou outro provedor com Pix e cartão.
- [ ] Criar intenção de pagamento exclusivamente no servidor.
- [ ] Integrar a tela nativa oficial do provedor.
- [ ] Validar a assinatura do webhook.
- [ ] Tornar o webhook a fonte do estado `paid`/`failed`.
- [ ] Cancelar ou devolver estoque de pedidos não pagos conforme uma política definida.
- [ ] Implementar reembolso e cancelamento administrativo.

Critério de conclusão: nenhum dado bruto de cartão passa pelo backend da EJM Santos,
e o pedido só aparece como pago após confirmação autenticada do provedor.

## Etapa 3 — Conta, segurança e privacidade

- [ ] Armazenar a sessão com criptografia apoiada pelo Android Keystore.
- [ ] Criar renovação e revogação de tokens.
- [ ] Adicionar recuperação de senha e verificação de e-mail.
- [ ] Limitar tentativas de login e cadastro.
- [ ] Permitir exclusão da conta e dos dados associados.
- [ ] Publicar política de privacidade e termos de compra.

Critério de conclusão: sessões podem ser encerradas pelo servidor e o cliente possui
os controles básicos sobre sua conta e seus dados.

## Etapa 4 — Operação e pós-venda

- [ ] Notificar mudanças de status do pedido.
- [ ] Exibir acompanhamento da entrega.
- [ ] Adicionar contato rápido com o atendimento.
- [ ] Permitir comprar novamente a partir do histórico.
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
