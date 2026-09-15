# EJM Santos — Android nativo

Aplicativo Android em Java/XML que consome a API Flask da EJM Santos. Não usa
WebView: telas, navegação, catálogo, carrinho e autenticação são componentes Android.

## Funcionalidades atuais

- catálogo em grade com busca;
- detalhes nativos dos produtos;
- imagens carregadas da API com cache em memória;
- carrinho persistente e controle de estoque;
- favoritos persistentes;
- cadastro e login via JWT;
- token de sessão criptografado com chave protegida pelo Android Keystore;
- recuperação de senha por código enviado por e-mail;
- alteração de senha com revogação das sessões anteriores;
- exclusão e anonimização da conta, mantendo o histórico operacional de pedidos;
- cadastro, seleção e remoção de endereços;
- checkout com endereço, cálculo de entrega e total validado pelo servidor;
- pedido com pagamento no recebimento, proteção contra duplicidade e baixa de estoque;
- cartão pelo Stripe PaymentSheet, com confirmação por webhook no backend;
- histórico de pedidos;
- acompanhamento visual das etapas de entrega;
- recompra pelo histórico com nova validação de preço e estoque;
- contato com o atendimento pelo WhatsApp ou e-mail;
- navegação inferior no estilo de aplicativos de marketplace.

## Compilar

No PowerShell, usando o Java que acompanha o Android Studio:

```powershell
$env:JAVA_HOME='C:\Program Files\Android\Android Studio\jbr'
.\gradlew.bat --no-daemon :app:testDebugUnitTest :app:assembleDebug
```

O APK será criado em `app/build/outputs/apk/debug/app-debug.apk`.

## Usar outra API

A URL padrão é a implantação no Render. Para apontar a build para outro servidor:

```powershell
.\gradlew.bat :app:assembleDebug -PEJM_API_BASE_URL=https://api.exemplo.com/
```

A URL deve terminar com `/`. Para produção, utilize sempre HTTPS.

Para abrir o WhatsApp do atendimento, informe o número no formato internacional,
somente com dígitos. Se ele não for informado, o app usa o e-mail de atendimento:

```powershell
.\gradlew.bat :app:assembleDebug `
  -PEJM_SUPPORT_WHATSAPP=5513999999999 `
  -PEJM_SUPPORT_EMAIL=contato@ejmsantos.com
```

## Backend necessário

Publique o backend Flask deste repositório antes de testar login, endereços e
pedidos. Esses recursos usam os endpoints `/api/mobile/*` adicionados ao backend.

## Próximas etapas

- verificar o endereço de e-mail e publicar política de privacidade e termos;
- notificações push de status do pedido;
- sincronização do carrinho entre dispositivos;
- testes instrumentados em emulador e preparação para a Play Store.
- por último, configurar as credenciais do Stripe e validar os pagamentos em modo de teste.

O planejamento e os critérios de conclusão estão em
[`docs/ROADMAP_APP_NATIVO.md`](../docs/ROADMAP_APP_NATIVO.md).
