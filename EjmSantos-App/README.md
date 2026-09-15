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
- cadastro, seleção e remoção de endereços;
- checkout com endereço, cálculo de entrega e total validado pelo servidor;
- pedido com pagamento no recebimento, proteção contra duplicidade e baixa de estoque;
- histórico de pedidos;
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

## Backend necessário

Publique o backend Flask deste repositório antes de testar login, endereços e
pedidos. Esses recursos usam os endpoints `/api/mobile/*` adicionados ao backend.

## Próximas etapas

- pagamento digital com Pix/cartão e confirmação por webhook;
- notificações de status do pedido;
- sincronização do carrinho entre dispositivos;
- testes instrumentados em emulador e preparação para a Play Store.

O planejamento e os critérios de conclusão estão em
[`docs/ROADMAP_APP_NATIVO.md`](../docs/ROADMAP_APP_NATIVO.md).
