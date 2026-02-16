# 🚚 Sistema de Taxa de Entrega por Distância

## Visão Geral

O sistema calcula automaticamente a taxa de entrega baseada na distância entre a loja e o endereço do cliente, usando **R$ 1,50 por quilômetro**, e permite que o admin **agende a data de entrega** para cada pedido.

## 📦 Fluxo de Pedido e Entrega

### 1. Cliente Finaliza Compra
- Taxa de entrega é calculada automaticamente
- Pedido é criado com status **"Pago"**
- Cliente vê mensagem: *"Aguardando confirmação de prazo de entrega"*

### 2. Admin Agenda Entrega
- Acessa painel admin → Pedidos
- Seleciona pedido específico
- Define **data e hora** da entrega
- Adiciona **observações** (opcional)
- Status muda para **"Agendado"**

### 3. Cliente Vê Data Agendada
- No histórico de pedidos aparece:
  - ✅ **Entrega agendada para:** DD/MM/YYYY às HH:MM
  - Observações (se houver)

### 4. Processo de Entrega
Status disponíveis:
- **Pendente** → Aguardando pagamento
- **Pago** → Pagamento confirmado, aguardando agendamento
- **Agendado** → Data de entrega definida
- **Saiu para Entrega** → Pedido está a caminho
- **Entregue** → Pedido foi entregue
- **Cancelado** → Pedido cancelado

## Como Funciona

### 1. Cálculo Automático
- Quando o cliente seleciona ou preenche um endereço no checkout, o sistema calcula automaticamente:
  - **Distância** entre a loja e o destino (em km)
  - **Taxa de entrega** (distância × R$ 1,50/km)
  - **Total** (subtotal dos produtos + taxa de entrega)

### 2. Geocodificação
- O sistema usa **OpenStreetMap Nominatim** (gratuito) para converter endereços em coordenadas
- Cálculo de distância usa a **fórmula de Haversine** (distância em linha reta)
- Se o endereço não puder ser geocodificado, usa **distância padrão de 5 km**

## Configuração

### 1. Definir Localização da Loja

Edite o arquivo [`config.py`](config.py) nas linhas 82-84:

```python
# Delivery / Entrega
DELIVERY_FEE_PER_KM = 1.50  # Taxa por km
STORE_ADDRESS = "Rua Principal, 100, Centro, São Paulo, SP"
STORE_COORDINATES = (-23.550520, -46.633308)  # (latitude, longitude)
```

**Como obter as coordenadas da sua loja:**
1. Acesse [Google Maps](https://www.google.com/maps)
2. Localize sua loja no mapa
3. Clique com botão direito no local exato
4. Selecione "Copiar coordenadas"
5. Cole em `STORE_COORDINATES` no formato `(latitude, longitude)`

### 2. Ajustar Taxa por Quilômetro

Para mudar o valor da taxa, altere `DELIVERY_FEE_PER_KM`:

```python
DELIVERY_FEE_PER_KM = 2.00  # R$ 2,00 por km
DELIVERY_FEE_PER_KM = 1.00  # R$ 1,00 por km
```

## Instalação

### 1. Instalar Dependências

```bash
pip install requests
```

Ou:

```bash
pip install -r requirements.txt
```

### 2. Atualizar Banco de Dados

Para adicionar as novas colunas à tabela `order`:

```bash
python add_delivery_columns.py
```

Ou recrie o banco (⚠️ apaga todos os dados):

```bash
python inicializar_db.py
```

## Estrutura Técnica

### Novos Campos no Model Order

```python
subtotal = db.Column(db.Float)                      # Total dos produtos
delivery_fee = db.Column(db.Float)                  # Taxa de entrega
delivery_distance_km = db.Column(db.Float)          # Distância em km
total = db.Column(db.Float)                         # Total = subtotal + delivery_fee

# Agendamento de entrega
delivery_date = db.Column(db.DateTime)              # Data/hora agendada para entrega
delivery_scheduled_at = db.Column(db.DateTime)      # Quando foi agendado
delivery_notes = db.Column(db.Text)                 # Observações sobre a entrega
```

## 🗓️ Agendamento de Entregas (Admin)

### Como Agendar uma Entrega

1. **Acesse o painel admin:**
   ```
   /admin/pedidos
   ```

2. **Clique no pedido desejado**

3. **Preencha o formulário de agendamento:**
   - 📅 **Data de Entrega** (obrigatório)
   - ⏰ **Horário** (padrão: 14:00)
   - 📝 **Observações** (opcional)
     - Ex: "Ligar antes de entregar"
     - Ex: "Entregar pela manhã"

4. **Clique em "Agendar Entrega"**
   - Status muda para **"Agendado"**
   - Cliente recebe email com data/hora
   - Informação aparece no histórico do cliente

### Reagendar Entrega

- Mesmo processo, basta alterar a data/hora
- Botão muda para "🔄 Reagendar Entrega"
- Data anterior é substituída

### Arquivos Modificados

1. **[`config.py`](config.py)** - Configurações de entrega e taxa por km
2. **[`app/models/order.py`](app/models/order.py)** - Campos de entrega e agendamento
3. **[`app/utils/distance.py`](app/utils/distance.py)** - ⭐ **NOVO** - Cálculo de distância
4. **[`app/routes/payment.py`](app/routes/payment.py)** - Endpoint `/calcular-entrega` e lógica de pagamento
5. **[`app/routes/admin.py`](app/routes/admin.py)** - Rota `/agendar-entrega` e atualização de status
6. **[`templates/checkout.html`](templates/checkout.html)** - Interface de checkout com taxa de entrega
7. **[`templates/admin_pedido_detalhe.html`](templates/admin_pedido_detalhe.html)** - Formulário de agendamento
8. **[`templates/perfil_novo.html`](templates/perfil_novo.html)** - Exibição de data agendada no histórico
9. **[`requirements.txt`](requirements.txt)** - Dependência `requests`
10. **[`add_delivery_columns.py`](add_delivery_columns.py)** - Script de migração

### API Endpoint

**POST `/calcular-entrega`**

Calcula taxa de entrega para um endereço.

**Request:**
```json
{
  "saved_address_id": 1  // OU
  "endereco": {
    "rua": "Rua das Flores",
    "numero": "123",
    "bairro": "Centro",
    "cidade": "São Paulo",
    "estado": "SP",
    "cep": "01234-567"
  }
}
```

**Response:**
```json
{
  "success": true,
  "distance_km": 12.5,
  "delivery_fee": 18.75,
  "fee_per_km": 1.50
}
```

## Interface do Cliente

### Checkout - Resumo do Pedido

```
Resumo do Pedido
─────────────────────────
Mel Silvestre (2x)  R$ 45,00
Mel Florada (1x)    R$ 25,00

Subtotal:           R$ 70,00
Entrega (12.5 km × R$ 1.50/km): R$ 18,75
─────────────────────────
Total:              R$ 88,75
```

### Cálculo em Tempo Real

- ✅ **Endereço salvo**: Calcula automaticamente ao selecionar
- ✅ **Novo endereço**: Calcula quando preencher a cidade
- ✅ **Atualização dinâmica**: Total atualiza em tempo real

### Histórico de Pedidos - Visão do Cliente

**Pedido Pago (Aguardando Agendamento):**
```
┌─────────────────────────────────────────┐
│ Pedido #123           [Pago]            │
│ 📅 16/02/2026 às 14:30                  │
│                                         │
│ ⏰ Aguardando confirmação de prazo      │
│    de entrega                           │
│                                         │
│ Mel Silvestre x2                        │
│ Mel Florada x1                          │
│                                         │
│ Total: R$ 88,75                         │
│ [Ver detalhes]                          │
└─────────────────────────────────────────┘
```

**Pedido Agendado:**
```
┌─────────────────────────────────────────┐
│ Pedido #123           [Agendado]        │
│ 📅 16/02/2026 às 14:30                  │
│                                         │
│ ✅ Entrega agendada:                    │
│    20/02/2026 às 15:00                  │
│                                         │
│ Mel Silvestre x2                        │
│ Mel Florada x1                          │
│                                         │
│ Total: R$ 88,75                         │
│ [Ver detalhes]                          │
└─────────────────────────────────────────┘
```

## Interface do Admin

### Painel de Agendamento

```
┌─────────────────────────────────────────────────┐
│ 🚚 Agendar Entrega                              │
├─────────────────────────────────────────────────┤
│                                                 │
│ ✅ Entrega Agendada para:                       │
│    20/02/2026 às 15:00                          │
│                                                 │
│    Observações: Ligar antes de entregar         │
│    Agendado em: 16/02/2026 14:45               │
│                                                 │
│ ─────────────────────────────────────────────── │
│                                                 │
│ 📅 Data de Entrega *                            │
│ [2026-02-20]                                    │
│                                                 │
│ ⏰ Horário *                                     │
│ [15:00]                                         │
│                                                 │
│ 📝 Observações                                   │
│ [Ligar antes de entregar...]                    │
│                                                 │
│ [🔄 Reagendar Entrega]                          │
└─────────────────────────────────────────────────┘
```

## Testes

### Teste Manual

1. Acesse `/checkout`
2. Selecione um endereço salvo → taxa deve aparecer
3. Ou preencha novo endereço → ao digitar cidade, taxa é calculada
4. Verifique que o total inclui a entrega
5. Finalize o pedido e confirme que foi salvo corretamente

### Teste da API

```bash
curl -X POST http://localhost:5000/calcular-entrega \
  -H "Content-Type: application/json" \
  -d '{
    "endereco": {
      "cidade": "São Paulo",
      "bairro": "Pinheiros"
    }
  }'
```

## Limitações e Melhorias Futuras

### Limitações Atuais

- ⚠️ **Distância em linha reta**: Não considera rotas reais de trânsito
- ⚠️ **Geocodificação limitada**: Endereços mal formatados podem falhar
- ⚠️ **Sem API key**: Nominatim gratuito tem limite de requisições

### Melhorias Possíveis

1. **Integração com Google Maps API**
   - Distância por rota real (não linha reta)
   - Tempo estimado de entrega
   - Requer API Key paga

2. **Zonas de entrega**
   - Definir bairros/regiões com taxa fixa
   - Taxa mínima de entrega
   - Frete grátis acima de valor X

3. **Cache de distâncias**
   - Salvar distâncias calculadas para endereços frequentes
   - Reduzir chamadas à API de geocodificação

## Suporte

Para problemas ou dúvidas:
1. Verifique os logs: `logs/app.log`
2. Teste o endpoint `/calcular-entrega` diretamente
3. Confirme que `STORE_COORDINATES` está correto em `config.py`

## Exemplo de Uso no Admin

Ao visualizar um pedido no admin, você verá:

```
Pedido #123
─────────────────────────
Subtotal:           R$ 70,00
Entrega (12.5 km):  R$ 18,75
Total:              R$ 88,75

📍 Endereço de Entrega:
Rua das Flores, 123
Centro - São Paulo, SP
```
