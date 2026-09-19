"""Testes dos metadados e filtros do catálogo."""

import os
import unittest

os.environ["FLASK_ENV"] = "testing"
os.environ.setdefault("EJM_SECRET", "test_secret_key_with_at_least_32_characters")

from application import Product, app, db
from app.utils.validators import Validator


class CatalogFilterTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
        self.client = app.test_client()
        with app.app_context():
            db.drop_all()
            db.create_all()
            db.session.add_all([
                Product(
                    titulo="Própolis verde",
                    descricao="Extrato de origem controlada",
                    preco=38.0,
                    estoque=8,
                    categoria="propolis",
                    origem="Minas Gerais",
                    beneficios="uso-diario,extrato",
                    sem_adicao_acucar=True,
                    destaque=True,
                ),
                Product(
                    titulo="Mel de laranjeira",
                    descricao="Sabor cítrico suave",
                    preco=45.0,
                    estoque=0,
                    categoria="mel",
                    origem="Interior de São Paulo",
                    beneficios="culinaria,energia",
                ),
            ])
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_filters_by_category_purpose_and_availability(self):
        response = self.client.get(
            "/api/products/search?categoria=propolis&finalidade=extrato&disponiveis=1"
        )
        self.assertEqual(response.status_code, 200)
        products = response.get_json()
        self.assertEqual([item["titulo"] for item in products], ["Própolis verde"])
        self.assertEqual(products[0]["beneficios"], ["uso-diario", "extrato"])

    def test_filters_without_added_sugar(self):
        response = self.client.get("/api/products/search?sem_adicao_acucar=1")
        self.assertEqual(response.status_code, 200)
        products = response.get_json()
        self.assertEqual(len(products), 1)
        self.assertTrue(products[0]["sem_adicao_acucar"])

    def test_search_includes_origin(self):
        response = self.client.get("/api/products/search?q=Minas")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()[0]["categoria"], "propolis")

    def test_medical_claims_are_rejected_in_product_copy(self):
        valid, errors = Validator.validate_product_data({
            "titulo": "Mel para diabetes",
            "descricao": "Promete tratamento",
            "preco": 20,
            "estoque": 1,
            "categoria": "mel",
            "beneficios": "uso-diario",
        })
        self.assertFalse(valid)
        self.assertTrue(any("benefício médico" in error for error in errors))

    def test_institutional_pages_are_available(self):
        expected = {
            "/entrega": "Entrega e prazos",
            "/trocas-e-devolucoes": "Trocas e devoluções",
            "/privacidade": "Política de privacidade",
            "/termos": "Termos de uso e compra",
        }
        for path, title in expected.items():
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertIn(title, response.get_data(as_text=True))

    def test_inline_scripts_receive_matching_csp_nonce(self):
        response = self.client.get("/carrinho")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        csp = response.headers["Content-Security-Policy"]
        marker = 'nonce="'
        self.assertIn(marker, html)
        nonce = html.split(marker, 1)[1].split('"', 1)[0]
        self.assertIn(f"'nonce-{nonce}'", csp)


if __name__ == "__main__":
    unittest.main()
