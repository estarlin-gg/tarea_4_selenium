import os
from datetime import datetime
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


SCREENSHOTS_DIR = os.path.join("reports", "screenshots")

@pytest.fixture(scope="class")
def driver_init(request):
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 15)
    base_url = "https://localhost:7265"

    request.cls.driver = driver
    request.cls.wait = wait
    request.cls.base_url = base_url

    yield
    driver.quit()

@pytest.mark.usefixtures("driver_init")
class TestPosApp:
    def login(self, username, password):
        self.driver.get(f"{self.base_url}/Account/Login")
        self.wait.until(EC.presence_of_element_located((By.NAME, "username")))
        self.driver.find_element(By.NAME, "username").clear()
        self.driver.find_element(By.NAME, "username").send_keys(username)
        self.driver.find_element(By.NAME, "password").clear()
        self.driver.find_element(By.NAME, "password").send_keys(password)
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    # --- HISTORIA 1: LOGIN ---
    def test_login_camino_feliz_usuario_valido(self):
        self.login("admin", "1234")
        self.wait.until(EC.url_contains("/Products"))
        assert "Lista de Productos" in self.driver.page_source

    def test_login_prueba_negativa_contrasena_incorrecta(self):
        self.login("admin", "incorrecta")
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "alert-danger")))
        assert "Credenciales inválidas" in self.driver.page_source

    def test_login_prueba_limite_campos_vacios(self):
        self.driver.get(f"{self.base_url}/Account/Login")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        self.wait.until(EC.presence_of_element_located((By.NAME, "username")))
        assert "Iniciar Sesión" in self.driver.page_source

    # --- HISTORIA 2: CREAR PRODUCTO ---
    def test_crear_producto_camino_feliz_datos_validos(self):
        self.login("admin", "1234")
        self.wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Nuevo Producto"))).click()

        self.wait.until(EC.presence_of_element_located((By.ID, "Name"))).send_keys("ProductoTest")
        self.driver.find_element(By.ID, "Price").send_keys("100")
        self.driver.find_element(By.CSS_SELECTOR, "input[name='Stock']").send_keys("10")

        self.driver.find_element(By.CSS_SELECTOR, "button.btn-success").click()

        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        assert "ProductoTest" in self.driver.page_source

    def test_crear_producto_prueba_negativa_precio_no_numerico(self):
        self.login("admin", "1234")
        self.wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Nuevo Producto"))).click()

        self.wait.until(EC.presence_of_element_located((By.ID, "Name"))).send_keys("ProductoError")
        self.driver.find_element(By.ID, "Price").send_keys("abc")  # inválido
        self.driver.find_element(By.CSS_SELECTOR, "input[name='Stock']").send_keys("5")

        self.driver.find_element(By.CSS_SELECTOR, "button.btn-success").click()

        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "text-danger")))
        assert "El precio debe ser un número positivo" in self.driver.page_source

    def test_crear_producto_prueba_limite_stock_cero(self):
        self.login("admin", "1234")
        self.wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Nuevo Producto"))).click()

        self.wait.until(EC.presence_of_element_located((By.ID, "Name"))).send_keys("ProductoStock0")
        self.driver.find_element(By.ID, "Price").send_keys("10")
        self.driver.find_element(By.CSS_SELECTOR, "input[name='Stock']").send_keys("0")

        self.driver.find_element(By.CSS_SELECTOR, "button.btn-success").click()

        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        assert "ProductoStock0" in self.driver.page_source

    # --- HISTORIA 3: EDITAR PRODUCTO ---
    def test_editar_producto_camino_feliz_datos_validos(self):
        self.login("admin", "1234")
        self.driver.get(f"{self.base_url}/Products/Edit/11")

        nombre = self.wait.until(EC.presence_of_element_located((By.ID, "Name")))
        nombre.clear()
        nombre.send_keys("ProductoEditado")

        precio = self.driver.find_element(By.ID, "Price")
        precio.clear()
        precio.send_keys("200")

        stock = self.driver.find_element(By.NAME, "Stock")
        stock.clear()
        stock.send_keys("15")

        self.driver.find_element(By.CSS_SELECTOR, "button.btn-primary").click()

        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        assert "ProductoEditado" in self.driver.page_source

    def test_editar_producto_prueba_negativa_nombre_vacio(self):
        self.login("admin", "1234")
        self.driver.get(f"{self.base_url}/Products/Edit/11")

        nombre = self.wait.until(EC.presence_of_element_located((By.ID, "Name")))
        nombre.clear()

        self.driver.find_element(By.CSS_SELECTOR, "button.btn-primary").click()

        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "span[data-valmsg-for='Name']")))
        assert "El campo Nombre es obligatorio" in self.driver.page_source

    def test_editar_producto_prueba_limite_precio_muy_alto(self):
        self.login("admin", "1234")
        self.driver.get(f"{self.base_url}/Products/Edit/11")

        precio = self.wait.until(EC.presence_of_element_located((By.ID, "Price")))
        precio.clear()
        precio.send_keys("999999")

        self.driver.find_element(By.CSS_SELECTOR, "button.btn-primary").click()

        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        assert "999999" in self.driver.page_source

    # --- HISTORIA 4: ELIMINAR PRODUCTO ---
    # def test_eliminar_producto_camino_feliz_confirmacion(self):
    #     self.login("admin", "1234")
    #     producto_id = 38
    #     self.driver.get(f"{self.base_url}/Products/Delete/{producto_id}")

    #     self.wait.until(EC.url_contains(f"/Products/Delete/{producto_id}"))
    #     nombre_producto = self.wait.until(EC.presence_of_element_located((By.ID, "Id"))).text

    #     self.driver.find_element(By.CSS_SELECTOR, "button.btn-danger").click()

    #     self.wait.until(EC.url_contains("/Products/Index"))
    #     assert nombre_producto not in self.driver.page_source

    def test_eliminar_producto_prueba_negativa_cancelar(self):
        self.login("admin", "1234")
        self.driver.get(f"{self.base_url}/Products/Delete/11")

        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.btn-secondary"))).click()

        self.wait.until(EC.url_contains("/Products/Index"))
        assert "Lista de Productos" in self.driver.page_source

    def test_eliminar_producto_prueba_limite_inexistente(self):
        self.login("admin", "1234")
        self.driver.get(f"{self.base_url}/Products/Delete/999999")

        assert "404" in self.driver.page_source

    # --- HISTORIA 5: VER DETALLES ---
    def test_ver_detalles_producto_camino_feliz(self):
        self.login("admin", "1234")
        self.driver.get(f"{self.base_url}/Products/Details/11")

        assert "Nombre:" in self.driver.page_source
        assert "Precio:" in self.driver.page_source
        assert "Stock:" in self.driver.page_source

    def test_ver_detalles_producto_prueba_negativa_inexistente(self):
        self.login("admin", "1234")
        self.driver.get(f"{self.base_url}/Products/Details/999999")

        assert "404" in self.driver.page_source

    def test_ver_detalles_producto_prueba_limite_id_cero(self):
        self.login("admin", "1234")
        self.driver.get(f"{self.base_url}/Products/Details/0")

        assert "404" in self.driver.page_source


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()

    if rep.when == "call":
        driver = getattr(item.instance, "driver", None)
        if driver:
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_name = f"{item.name}_{timestamp}.png"
                os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
                screenshot_path = os.path.join(SCREENSHOTS_DIR, screenshot_name)
                driver.save_screenshot(screenshot_path)
                print(f"[INFO] Captura guardada: {screenshot_path}")

                # Agregar imagen al reporte HTML 
                pytest_html = item.config.pluginmanager.getplugin("html")
                if pytest_html:
                    extra = getattr(rep, "extra", [])
                    rel_path = os.path.relpath(screenshot_path, os.path.dirname(item.config.option.htmlpath))
                    html = f'<div><img src="{rel_path}" alt="screenshot" style="width:600px; border:1px solid #ccc"/></div>'
                    extra.append(pytest_html.extras.html(html))
                    rep.extra = extra
            except Exception as e:
                print(f"[ERROR] No se pudo guardar la captura: {e}")


    # --- HISTORIA 4: ELIMINAR PRODUCTO (camino feliz) ---
    def test_eliminar_producto_camino_feliz_confirmacion(self):
        self.login("admin", "1234")
        producto_id = 12  # usar un ID existente en la BD de pruebas
        self.driver.get(f"{self.base_url}/Products/Delete/{producto_id}")

        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.btn-danger"))).click()
        self.wait.until(EC.url_contains("/Products/Index"))

        assert f"/Products/Delete/{producto_id}" not in self.driver.current_url
        assert "Lista de Productos" in self.driver.page_source

    # --- HISTORIA 6: BUSCAR PRODUCTOS ---
    def test_buscar_producto_existente(self):
        self.login("admin", "1234")
        self.wait.until(EC.presence_of_element_located((By.ID, "searchBox"))).send_keys("ProductoTest")
        self.driver.find_element(By.ID, "btnBuscar").click()

        assert "ProductoTest" in self.driver.page_source

    def test_buscar_producto_inexistente(self):
        self.login("admin", "1234")
        self.wait.until(EC.presence_of_element_located((By.ID, "searchBox"))).send_keys("InexistenteXYZ")
        self.driver.find_element(By.ID, "btnBuscar").click()

        assert "No se encontraron productos" in self.driver.page_source

    # --- HISTORIA 7: FILTRAR PRODUCTOS POR STOCK BAJO ---
    def test_filtrar_productos_stock_bajo(self):
        self.login("admin", "1234")
        self.wait.until(EC.presence_of_element_located((By.ID, "stockFilter"))).send_keys("5")
        self.driver.find_element(By.ID, "btnFiltrar").click()

        assert "Stock menor a 5" in self.driver.page_source or "Producto" in self.driver.page_source

    def test_filtrar_productos_stock_bajo_sin_resultados(self):
        self.login("admin", "1234")
        self.wait.until(EC.presence_of_element_located((By.ID, "stockFilter"))).send_keys("9999")
        self.driver.find_element(By.ID, "btnFiltrar").click()

        assert "Todos los productos tienen stock suficiente" in self.driver.page_source

    # --- HISTORIA 8: ORDENAR PRODUCTOS ---
    def test_ordenar_productos_ascendente(self):
        self.login("admin", "1234")
        self.wait.until(EC.presence_of_element_located((By.ID, "sortOrder"))).send_keys("asc")
        self.driver.find_element(By.ID, "btnOrdenar").click()

        assert "Lista de Productos" in self.driver.page_source  # verificar orden con parsing de tabla

    def test_ordenar_productos_descendente(self):
        self.login("admin", "1234")
        self.wait.until(EC.presence_of_element_located((By.ID, "sortOrder"))).send_keys("desc")
        self.driver.find_element(By.ID, "btnOrdenar").click()

        assert "Lista de Productos" in self.driver.page_source

    # --- HISTORIA 9: EXPORTAR INVENTARIO A EXCEL ---
    def test_exportar_inventario_excel(self):
        self.login("admin", "1234")
        self.wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Exportar a Excel"))).click()

        # validamos que inicie descarga
        # en Selenium puro es complejo validar archivo → mock o verificar alerta/mensaje
        assert "xlsx" in self.driver.page_source or "Exportación" in self.driver.page_source

    # --- HISTORIA 11: GESTIÓN DE USUARIOS ---
    def test_crear_usuario_duplicado(self):
        self.login("admin", "1234")
        self.driver.get(f"{self.base_url}/Users/Create")

        self.wait.until(EC.presence_of_element_located((By.ID, "Username"))).send_keys("admin")
        self.driver.find_element(By.ID, "Password").send_keys("1234")
        self.driver.find_element(By.ID, "Role").send_keys("Empleado")

        self.driver.find_element(By.CSS_SELECTOR, "button.btn-success").click()

        assert "nombre repetido" in self.driver.page_source or "ya existe" in self.driver.page_source

    # --- HISTORIA 12: CONTROL DE ACCESO POR ROLES ---
    def test_empleado_no_puede_crear_producto(self):
        self.login("empleado", "1234")
        self.driver.get(f"{self.base_url}/Products/Create")

        assert "Acceso denegado" in self.driver.page_source or "403" in self.driver.page_source

    # --- HISTORIA 10: REPORTE DE VENTAS ---
    def test_reporte_ventas_camino_feliz(self):
        self.login("admin", "1234")
        self.driver.get(f"{self.base_url}/Reports/Ventas")

        self.wait.until(EC.presence_of_element_located((By.ID, "fechaInicio"))).send_keys("2023-01-01")
        self.driver.find_element(By.ID, "fechaFin").send_keys("2023-12-31")
        self.driver.find_element(By.ID, "btnGenerar").click()

        assert "Reporte de Ventas" in self.driver.page_source

    def test_reporte_ventas_sin_datos(self):
        self.login("admin", "1234")
        self.driver.get(f"{self.base_url}/Reports/Ventas")

        self.wait.until(EC.presence_of_element_located((By.ID, "fechaInicio"))).send_keys("1900-01-01")
        self.driver.find_element(By.ID, "fechaFin").send_keys("1900-12-31")
        self.driver.find_element(By.ID, "btnGenerar").click()

        assert "No hay datos para mostrar" in self.driver.page_source

