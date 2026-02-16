# ============================================
# utils/distance.py — Cálculo de Distância
# ============================================

import math
import requests
from typing import Tuple, Optional


def haversine_distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """
    Calcula a distância entre dois pontos usando a fórmula de Haversine.
    
    Args:
        coord1: Tupla (latitude, longitude) do primeiro ponto
        coord2: Tupla (latitude, longitude) do segundo ponto
    
    Returns:
        Distância em quilômetros
    """
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    
    # Raio da Terra em km
    R = 6371.0
    
    # Converter para radianos
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Diferenças
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Fórmula de Haversine
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    distance = R * c
    return round(distance, 2)


def geocode_address(address: str) -> Optional[Tuple[float, float]]:
    """
    Converte um endereço em coordenadas usando Nominatim (OpenStreetMap).
    
    Args:
        address: Endereço completo como string
    
    Returns:
        Tupla (latitude, longitude) ou None se não encontrado
    """
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': address,
            'format': 'json',
            'limit': 1
        }
        headers = {
            'User-Agent': 'EJM-Santos-Mel/1.0'  # Nominatim requer User-Agent
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                return (lat, lon)
        
        return None
    
    except Exception as e:
        print(f"Erro ao geocodificar endereço: {str(e)}")
        return None


def calculate_delivery_fee(
    origin_coords: Tuple[float, float],
    destination_address: str,
    fee_per_km: float = 1.50
) -> Tuple[float, float]:
    """
    Calcula a taxa de entrega baseada na distância.
    
    Args:
        origin_coords: Coordenadas da loja (latitude, longitude)
        destination_address: Endereço de destino completo
        fee_per_km: Taxa por quilômetro (padrão R$ 1.50)
    
    Returns:
        Tupla (distância_km, taxa_entrega)
    """
    # Geocodificar endereço de destino
    dest_coords = geocode_address(destination_address)
    
    if not dest_coords:
        # Se não conseguir geocodificar, retorna distância estimada padrão
        # Pode ser ajustado conforme necessidade
        default_distance = 5.0
        return (default_distance, default_distance * fee_per_km)
    
    # Calcular distância
    distance = haversine_distance(origin_coords, dest_coords)
    
    # Calcular taxa
    delivery_fee = distance * fee_per_km
    
    return (distance, round(delivery_fee, 2))


def format_endereco_completo(endereco: dict) -> str:
    """
    Formata um dicionário de endereço em string completa para geocodificação.
    
    Args:
        endereco: Dicionário com campos rua, numero, bairro, cidade, etc.
    
    Returns:
        String formatada do endereço
    """
    partes = []
    
    if endereco.get('rua') and endereco.get('numero'):
        partes.append(f"{endereco['rua']}, {endereco['numero']}")
    
    if endereco.get('bairro'):
        partes.append(endereco['bairro'])
    
    if endereco.get('cidade'):
        partes.append(endereco['cidade'])
    
    if endereco.get('estado'):
        partes.append(endereco['estado'])
    
    if endereco.get('cep'):
        partes.append(endereco['cep'])
    
    # Se não tiver informação suficiente, adicionar "Brasil" para ajudar na geocodificação
    if partes:
        partes.append('Brasil')
    
    return ', '.join(partes)
