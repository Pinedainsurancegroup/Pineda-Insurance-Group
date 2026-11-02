# Recuperación de fuentes en el alcance autorizado

Se inspeccionaron 305 commits alcanzables y 550 blobs del historial local disponible, más nombres históricos de fuente y metadatos ZIP. Inventario completo: history-recovery-inventory.json y historical-source-paths.json. No es búsqueda en GitHub privado ni auditoría de objetos borrados/inaccesibles.

Recuperación concreta: /workspace/recovered-pag/pag-crm-bridge-source.tar, commit fbbe987e83ae4b4153f1dfe4d7bc051ca80f69bc, ruta pag-leads-bridge. SHA256 324c9aa1327916d79a2afae3f6770796a55cbc08ba7a89f2d5de13e0a2eb08f7; 15 miembros de archivo/directorio. Incluye bridge.cjs, integration-controls.cjs, preview.cjs, audit.cjs, cinco archivos de suite y documentación. Las 161 pruebas pasan localmente.

Esto recupera el puente de proyección/controles y su evidencia; no un servidor CRM completo. Las menciones de PAG AI, PAG CRM y Receiver restantes se localizaron en documentos/contratos. No se identificaron fuentes completas desplegables de PAG AI, CRM v22 ni Receiver v23 en las ramas/historial/artefactos examinados. La ausencia en ese alcance no demuestra que no existan en repositorios privados, Apps Script u otros servicios.

El ZIP histórico pineda-insurance-site.zip solo contiene index.html; CRC válido, no fuente backend. Los fragmentos Taty Nails conocidos corresponden a su app Android y no se clasifican como CRM/AI/Receiver. Materiales de firma encontrados por nombre se excluyeron de lectura/decodificación y del paquete recuperado.

Se localizó además una semilla histórica de actualización Android: pag-leads-android/tests/make-upgrade-fixture.py, última adición/modificación localizada 7f49eb59f5d26f64a3cdde2b0f1acc2cca1feba9. Usa el ID estable y una firma de CI desechable: NO ejecutarla/instalarla en el teléfono con versiones estables. Haría falta adaptar el ID a .staging y usar fixtures de datos permitidos, misma firma de prueba y dispositivo dedicado antes de comprobar migración. No se ejecutó ni compiló esa semilla.

No se inventaron repositorios ni endpoints para reemplazar las fuentes faltantes. ACCESS-CHECKLIST.md indica dónde solicitar la URL exacta y acceso de lectura, con contratos/datasets de pruebas, sin credenciales en chat.
