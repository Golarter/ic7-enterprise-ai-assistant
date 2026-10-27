"""Regresiones de clasificación y telemetría CloudWatch."""
import logging
from app.agent import classify_priority
from cloud_aws.api import log


def test_incidente_empresa_autenticacion_es_critico():
    description = ('Clasifica la prioridad: el sistema de autenticación de toda '
                   'la empresa está caído y ningún empleado puede ingresar.')
    assert classify_priority(description)['prioridad'] == 'Crítica'


def test_caida_plataforma_completa_es_critica():
    assert classify_priority('Caída total de la plataforma principal')['prioridad'] == 'Crítica'


def test_ransomware_sigue_siendo_critico():
    assert classify_priority('Posible ransomware')['prioridad'] == 'Crítica'


def test_acceso_individual_no_es_critico():
    assert classify_priority('Un usuario está sin acceso a la VPN')['prioridad'] == 'Alta'


def test_actualizacion_es_media():
    assert classify_priority('Actualizar inventario')['prioridad'] == 'Media'


def test_consulta_informativa_es_baja():
    assert classify_priority('Solicitud de información')['prioridad'] == 'Baja'


def test_logger_ic7_permite_info():
    assert log.name == 'enterprise.aws'
    assert log.isEnabledFor(logging.INFO)
