"""Perfil, personalización inicial, tutorial, idioma y foto."""
import io

from PIL import Image

from tests.conftest import PASSWORD_VALIDA


def _imagen(formato="PNG", tam=(300, 200), modo="RGB") -> bytes:
    buf = io.BytesIO()
    Image.new(modo, tam, (200, 30, 30)).save(buf, format=formato)
    return buf.getvalue()


def _subir(client, usuario, contenido, nombre="f.png", tipo="image/png"):
    return client.put("/usuarios/me/foto", headers=usuario.headers, files={"archivo": (nombre, contenido, tipo)})


# ---------- Estado inicial / flujo de primer uso ----------
def test_usuario_nuevo_empieza_sin_configuracion(client, usuario_a):
    d = client.get("/usuarios/me", headers=usuario_a.headers).json()
    assert d["idioma"] == "es"
    assert d["personalizacion_completada"] is False
    assert d["tutorial_completado"] is False
    assert d["tiene_foto"] is False
    assert "password" not in str(d).lower()


def test_preferencia_por_defecto_no_crea_fila(client, usuario_a, db):
    r = client.get("/usuarios/me/preferencia-notificacion", headers=usuario_a.headers)
    assert r.json() == {"perfil_recordatorios": "equilibrado", "notificaciones_activas": True}
    assert client.get("/usuarios/me", headers=usuario_a.headers).json()["personalizacion_completada"] is False


def test_guardar_preferencia_completa_personalizacion_y_persiste_tras_relogin(client, usuario_a):
    r = client.put(
        "/usuarios/me/preferencia-notificacion",
        headers=usuario_a.headers,
        json={"perfil_recordatorios": "insistente", "notificaciones_activas": True},
    )
    assert r.status_code == 200 and r.json()["perfil_recordatorios"] == "insistente"
    # Nueva sesión (login otra vez): el estado viene del servidor.
    t = client.post("/auth/login", json={"email": usuario_a.email, "password": PASSWORD_VALIDA}).json()
    h = {"Authorization": f"Bearer {t['access_token']}"}
    assert client.get("/usuarios/me", headers=h).json()["personalizacion_completada"] is True
    assert client.get("/usuarios/me/preferencia-notificacion", headers=h).json()["perfil_recordatorios"] == "insistente"


def test_preferencia_invalida_se_rechaza(client, usuario_a):
    for cuerpo in ({"perfil_recordatorios": "extremo"}, {}, {"perfil_recordatorios": "tranquilo", "x": 1}):
        r = client.put("/usuarios/me/preferencia-notificacion", headers=usuario_a.headers, json=cuerpo)
        assert r.status_code == 422, cuerpo
    assert client.get("/usuarios/me", headers=usuario_a.headers).json()["personalizacion_completada"] is False


def test_cambiar_preferencia_no_reescribe_la_fecha_de_completado(client, usuario_a):
    p = lambda perfil: client.put(
        "/usuarios/me/preferencia-notificacion", headers=usuario_a.headers, json={"perfil_recordatorios": perfil}
    )
    p("tranquilo")
    f1 = client.get("/usuarios/me", headers=usuario_a.headers).json()["personalizacion_completada_en"]
    p("insistente")
    assert client.get("/usuarios/me", headers=usuario_a.headers).json()["personalizacion_completada_en"] == f1


def test_tutorial_se_completa_una_vez_e_idempotente(client, usuario_a):
    r1 = client.post("/usuarios/me/tutorial/completar", headers=usuario_a.headers)
    r2 = client.post("/usuarios/me/tutorial/completar", headers=usuario_a.headers)
    assert r1.status_code == r2.status_code == 200
    assert r1.json()["tutorial_completado"] is True
    assert r1.json()["tutorial_completado_en"] == r2.json()["tutorial_completado_en"]


def test_endpoints_requieren_autenticacion(client):
    for metodo, ruta in [
        ("get", "/usuarios/me/preferencia-notificacion"),
        ("put", "/usuarios/me/preferencia-notificacion"),
        ("post", "/usuarios/me/tutorial/completar"),
        ("patch", "/usuarios/me"),
        ("get", "/usuarios/me/foto"),
        ("put", "/usuarios/me/foto"),
        ("delete", "/usuarios/me/foto"),
    ]:
        assert getattr(client, metodo)(ruta).status_code == 401, (metodo, ruta)


def test_configuracion_de_un_usuario_no_afecta_a_otro(client, usuario_a, usuario_b):
    client.put("/usuarios/me/preferencia-notificacion", headers=usuario_a.headers, json={"perfil_recordatorios": "tranquilo"})
    client.post("/usuarios/me/tutorial/completar", headers=usuario_a.headers)
    d = client.get("/usuarios/me", headers=usuario_b.headers).json()
    assert d["personalizacion_completada"] is False and d["tutorial_completado"] is False
    assert client.get("/usuarios/me/preferencia-notificacion", headers=usuario_b.headers).json()["perfil_recordatorios"] == "equilibrado"


# ---------- Nombre ----------
def test_cambiar_nombre_persiste(client, usuario_a):
    r = client.patch("/usuarios/me", headers=usuario_a.headers, json={"nombre": "  María   José  "})
    assert r.status_code == 200 and r.json()["nombre"] == "María José"
    t = client.post("/auth/login", json={"email": usuario_a.email, "password": PASSWORD_VALIDA}).json()
    assert client.get("/usuarios/me", headers={"Authorization": f"Bearer {t['access_token']}"}).json()["nombre"] == "María José"


def test_nombre_invalido(client, usuario_a):
    for n in ("", " ", "A", "x" * 101, "Ana<script>", "Ana123"):
        r = client.patch("/usuarios/me", headers=usuario_a.headers, json={"nombre": n})
        assert r.status_code == 422, n
        assert r.json()["error"]["codigo"] == "VALIDACION"


def test_no_se_puede_editar_correo_ni_otros_campos(client, usuario_a, usuario_b):
    for cuerpo in ({"email": "otro@x.com"}, {"id_usuario": str(usuario_b.id)}, {"zona_horaria": "UTC"}, {"password": "x"}):
        assert client.patch("/usuarios/me", headers=usuario_a.headers, json=cuerpo).status_code == 422
    assert client.get("/usuarios/me", headers=usuario_a.headers).json()["email"] == usuario_a.email


def test_patch_solo_modifica_el_perfil_propio(client, usuario_a, usuario_b):
    client.patch("/usuarios/me", headers=usuario_a.headers, json={"nombre": "Ana Perez"})
    assert client.get("/usuarios/me", headers=usuario_b.headers).json()["nombre"] is None


# ---------- Idioma ----------
def test_cambiar_idioma_persiste_y_valida(client, usuario_a):
    assert client.patch("/usuarios/me", headers=usuario_a.headers, json={"idioma": "en"}).json()["idioma"] == "en"
    t = client.post("/auth/login", json={"email": usuario_a.email, "password": PASSWORD_VALIDA}).json()
    h = {"Authorization": f"Bearer {t['access_token']}"}
    assert client.get("/usuarios/me", headers=h).json()["idioma"] == "en"
    assert client.patch("/usuarios/me", headers=h, json={"idioma": "fr"}).status_code == 422
    assert client.patch("/usuarios/me", headers=h, json={"idioma": "es"}).json()["idioma"] == "es"


def test_cambiar_idioma_no_borra_el_nombre(client, usuario_a):
    client.patch("/usuarios/me", headers=usuario_a.headers, json={"nombre": "Ana Perez"})
    r = client.patch("/usuarios/me", headers=usuario_a.headers, json={"idioma": "en"})
    assert r.json()["nombre"] == "Ana Perez"


# ---------- Foto ----------
def test_foto_subir_ver_cambiar_borrar(client, usuario_a):
    assert client.get("/usuarios/me/foto", headers=usuario_a.headers).status_code == 404
    r = _subir(client, usuario_a, _imagen("PNG", (300, 200)))
    assert r.status_code == 200 and r.json()["tiene_foto"] is True
    g = client.get("/usuarios/me/foto", headers=usuario_a.headers)
    assert g.status_code == 200 and g.headers["content-type"] == "image/jpeg"
    img = Image.open(io.BytesIO(g.content))
    assert img.format == "JPEG" and img.size == (512, 512)
    # Cambiar por otra
    _subir(client, usuario_a, _imagen("JPEG", (100, 100)), "x.jpg", "image/jpeg")
    assert client.get("/usuarios/me/foto", headers=usuario_a.headers).status_code == 200
    # Borrar
    d = client.delete("/usuarios/me/foto", headers=usuario_a.headers)
    assert d.status_code == 200 and d.json()["tiene_foto"] is False
    assert client.get("/usuarios/me/foto", headers=usuario_a.headers).status_code == 404


def test_foto_persiste_tras_relogin(client, usuario_a):
    _subir(client, usuario_a, _imagen("WEBP"), "a.webp", "image/webp")
    t = client.post("/auth/login", json={"email": usuario_a.email, "password": PASSWORD_VALIDA}).json()
    h = {"Authorization": f"Bearer {t['access_token']}"}
    assert client.get("/usuarios/me", headers=h).json()["tiene_foto"] is True
    assert client.get("/usuarios/me/foto", headers=h).status_code == 200


def test_foto_formato_invalido_se_rechaza(client, usuario_a):
    # Texto con extensión y Content-Type de imagen: no se confía en lo que declara el cliente.
    r = _subir(client, usuario_a, b"esto no es una imagen", "falsa.png", "image/png")
    assert r.status_code == 422 and r.json()["error"]["codigo"] == "FOTO_INVALIDA"
    # Imagen real pero de un formato no permitido (GIF / BMP) aunque diga ser jpeg.
    for fmt in ("GIF", "BMP"):
        r = _subir(client, usuario_a, _imagen(fmt, (10, 10), "P" if fmt == "GIF" else "RGB"), "a.jpg", "image/jpeg")
        assert r.status_code == 422 and r.json()["error"]["codigo"] == "FOTO_FORMATO_INVALIDO"
    # SVG / HTML con script
    r = _subir(client, usuario_a, b"<svg onload=alert(1)></svg>", "a.svg", "image/svg+xml")
    assert r.status_code == 422
    assert client.get("/usuarios/me", headers=usuario_a.headers).json()["tiene_foto"] is False


def test_foto_vacia_truncada_y_demasiado_grande(client, usuario_a):
    assert _subir(client, usuario_a, b"").status_code == 422
    assert _subir(client, usuario_a, _imagen("PNG", (400, 400))[:200]).status_code == 422
    r = _subir(client, usuario_a, b"\x89PNG" + b"0" * (5 * 1024 * 1024 + 10))
    assert r.status_code == 413 and r.json()["error"]["codigo"] == "FOTO_DEMASIADO_GRANDE"


def test_foto_sin_archivo(client, usuario_a):
    assert client.put("/usuarios/me/foto", headers=usuario_a.headers).status_code == 422


def test_foto_se_reencodifica_sin_exif(client, usuario_a):
    buf = io.BytesIO()
    exif = Image.Exif()
    exif[0x010E] = "DATO-PRIVADO-GPS"
    Image.new("RGB", (64, 64), (1, 2, 3)).save(buf, format="JPEG", exif=exif)
    assert b"DATO-PRIVADO-GPS" in buf.getvalue()
    _subir(client, usuario_a, buf.getvalue(), "a.jpg", "image/jpeg")
    salida = client.get("/usuarios/me/foto", headers=usuario_a.headers).content
    assert b"DATO-PRIVADO-GPS" not in salida


def test_foto_con_transparencia(client, usuario_a):
    assert _subir(client, usuario_a, _imagen("PNG", (50, 50), "RGBA")).status_code == 200


def test_foto_de_un_usuario_no_es_visible_ni_afecta_a_otro(client, usuario_a, usuario_b):
    _subir(client, usuario_a, _imagen())
    assert client.get("/usuarios/me/foto", headers=usuario_b.headers).status_code == 404
    assert client.delete("/usuarios/me/foto", headers=usuario_b.headers).status_code == 200  # solo toca la suya
    assert client.get("/usuarios/me/foto", headers=usuario_a.headers).status_code == 200
