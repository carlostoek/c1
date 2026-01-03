# REQUERIMIENTO: FASE 4 - EL GABINETE
## Proyecto: El Mayordomo del Diván
## Bot de Telegram para Señorita Kinky

---

# CONTEXTO

El Gabinete no es una tienda. Es el espacio personal de Lucien donde guarda objetos que Diana ha autorizado para intercambio. Cada item tiene historia, cada compra tiene ritual, cada categoría tiene significado.

**Principio fundamental:** Comprar en el Gabinete debe sentirse como un privilegio, no como una transacción comercial. Lucien no es un vendedor - es un curador que decide qué mostrar a quién.

**Dependencias:**
- Fase 0 completada (items definidos, categorías)
- Fase 2 completada 
- Fase 3
---

# ARQUITECTURA DEL GABINETE

## Categorías

| ID | Nombre Display | Emoji | Descripción de Lucien |
|----|---------------|-------|----------------------|
| ephemeral | Efímeros | ⚡ | "Placeres de un solo uso. Intensos pero fugaces. Como ciertos momentos con Diana." |
| distinctive | Distintivos | 🎖️ | "Marcas visibles de su posición en este universo. Para quienes valoran el reconocimiento público." |
| keys | Llaves | 🔑 | "Abren puertas a contenido que otros no pueden ver. El conocimiento tiene precio." |
| relics | Reliquias | 💎 | "Los objetos más valiosos del Gabinete. Requieren Besitos considerables... y dignidad demostrada." |

## Niveles de acceso por categoría

| Categoría | Nivel mínimo para ver | Nivel mínimo para comprar |
|-----------|----------------------|--------------------------|
| Efímeros | 1 (Visitante) | 1 (Visitante) |
| Distintivos | 1 (Visitante) | 2 (Observado) |
| Llaves | 2 (Observado) | 3 (Evaluado) |
| Reliquias | 4 (Reconocido) | 5 (Admitido) |

**Nota:** Usuarios pueden VER categorías de nivel superior pero no comprar. Esto genera aspiración.

---

# F4.1: CATÁLOGO COMPLETO DE ITEMS

## Categoría: EFÍMEROS (ephemeral)

Items de un solo uso que expiran o se consumen.

### eph_001: Sello del Día
```
Nombre: "Sello del Día"
Precio: 1 Favor
Tipo: Consumible temporal
Duración: 24 horas
Nivel requerido: 1

Descripción Lucien:
"Una marca temporal que indica actividad reciente. Válida hasta medianoche.
Algunos lo consideran un ritual diario. Otros, una vanidad menor."

Efecto técnico:
- Badge temporal visible en perfil por 24h
- Pequeño indicador junto al nombre en interacciones

Mensaje al comprar:
"El Sello ha sido aplicado. Por las próximas horas, su presencia será... marcada.
Use este tiempo sabiamente."
```

### eph_002: Susurro Efímero
```
Nombre: "Susurro Efímero"
Precio: 3 Besitos
Tipo: Contenido único
Duración: Reproducción única
Nivel requerido: 1

Descripción Lucien:
"Un mensaje de voz que Diana grabó en un momento de... inspiración.
15 segundos. Una vez. Luego se desvanece como si nunca hubiera existido."

Efecto técnico:
- Desbloquea audio exclusivo de 15 segundos
- Solo se puede reproducir 1 vez (o 3 veces en 24h, decidir)
- Después desaparece del inventario

Mensaje al comprar:
"El Susurro es suyo. Escúchelo cuando esté... preparado.
No habrá repetición. Diana no se repite."

Mensaje al reproducir:
"Presione para escuchar. Este momento no se repetirá."

Mensaje después de reproducir:
"El Susurro se ha desvanecido. Como estaba destinado.
¿Valió la pena? Solo usted lo sabe."
```

### eph_003: Pase de Prioridad
```
Nombre: "Pase de Prioridad"
Precio: 5 Besitos
Tipo: Beneficio único
Duración: Hasta próximo contenido limitado
Nivel requerido: 2

Descripción Lucien:
"Cuando Diana libere contenido de acceso limitado, usted estará primero en la fila.
No garantiza acceso - garantiza oportunidad."

Efecto técnico:
- Flag en usuario: priority_pass = True
- Cuando hay contenido limitado, usuarios con pase reciben notificación primero
- El pase se consume cuando se usa (o expira en 30 días)

Mensaje al comprar:
"El Pase es suyo. Cuando Diana decida abrir algo exclusivo, 
usted será notificado antes que los demás.
La ventaja del tiempo... no es poca cosa."
```

### eph_004: Vistazo al Sensorium
```
Nombre: "Vistazo al Sensorium"
Precio: 15 Besitos
Tipo: Contenido preview
Duración: 48 horas para ver
Nivel requerido: 3

Descripción Lucien:
"Una muestra del contenido Sensorium. Treinta segundos diseñados para 
alterar su percepción sensorial.
Diana pasó meses estudiando cómo el cerebro procesa el placer.
Este es un fragmento de ese conocimiento."

Efecto técnico:
- Desbloquea preview de 30 segundos de contenido Sensorium
- Disponible por 48 horas después de compra
- Después se bloquea (incentivo a comprar acceso completo)

Mensaje al comprar:
"El Vistazo está desbloqueado. Tiene 48 horas.
Le sugiero un espacio tranquilo. Auriculares. Sin distracciones.
Esto no es contenido convencional."
```

### eph_005: Confesión Nocturna
```
Nombre: "Confesión Nocturna"
Precio: 8 Besitos
Tipo: Contenido exclusivo
Duración: Una lectura
Nivel requerido: 2

Descripción Lucien:
"Un texto que Diana escribió tarde en la noche. Pensamientos que 
normalmente no comparte. Una confesión entre ella y la oscuridad.
Ahora, entre ella y usted."

Efecto técnico:
- Desbloquea texto exclusivo (200-400 palabras)
- Formato especial: fondo oscuro, tipografía íntima
- Una vez leído, permanece pero marcado como "leído"

Mensaje al comprar:
"La Confesión está disponible. Diana no sabe que la compró.
O quizás sí. Nunca se sabe con ella."
```

---

## Categoría: DISTINTIVOS (distinctive)

Badges permanentes que muestran estatus.

### dist_001: Sello del Visitante
```
Nombre: "Sello del Visitante"
Precio: 2 Besitos
Tipo: Badge permanente
Nivel requerido: 1

Descripción Lucien:
"La marca más básica. Indica que existe en este universo y decidió 
hacerlo oficial. No es mucho. Pero es un comienzo."

Efecto técnico:
- Badge permanente en perfil
- Emoji: 👁️
- Visible en interacciones

Mensaje al comprar:
"El Sello está grabado. Ahora es oficialmente parte del registro.
Diana podrá ver esta marca cuando revise... si revisa."
```

### dist_002: Insignia del Observador
```
Nombre: "Insignia del Observador"
Precio: 5 Besitos
Tipo: Badge permanente
Nivel requerido: 2

Descripción Lucien:
"Lucien lo ha notado. Esta insignia lo certifica.
¿Significa algo? Para algunos, todo. Para otros, nada.
Depende de cuánto valore ser visto."

Efecto técnico:
- Badge permanente de nivel 2
- Emoji: 🔍
- Requisito previo: Tener dist_001 o nivel 2+

Mensaje al comprar:
"La Insignia es suya. A partir de ahora, cuando yo observe el registro,
su nombre tendrá esta marca. No es poco."
```

### dist_003: Marca del Evaluado
```
Nombre: "Marca del Evaluado"
Precio: 8 Besitos
Tipo: Badge permanente
Nivel requerido: 3

Descripción Lucien:
"Ha pasado las primeras pruebas. Esta marca lo atestigua.
No todas las pruebas. Pero las suficientes para merecer reconocimiento."

Efecto técnico:
- Badge permanente de nivel 3
- Emoji: ✓
- Requisito: Nivel 3+ alcanzado

Mensaje al comprar:
"La Marca está aplicada. Cuando otros vean su perfil, sabrán 
que no es un visitante casual. Es alguien... evaluado."
```

### dist_004: Emblema del Reconocido
```
Nombre: "Emblema del Reconocido"
Precio: 12 Besitos
Tipo: Badge permanente
Nivel requerido: 4

Descripción Lucien:
"Diana sabe su nombre. Este emblema lo confirma públicamente.
No es algo que se otorgue fácilmente. Usted lo ganó."

Efecto técnico:
- Badge permanente de nivel 4
- Emoji: ⭐
- Requisito: Nivel 4+ alcanzado
- Pequeño bonus: +5% descuento adicional en Gabinete

Mensaje al comprar:
"El Emblema brilla en su perfil. Diana lo reconoce.
Eso conlleva privilegios. Y expectativas."
```

### dist_005: Marca del Confidente
```
Nombre: "Marca del Confidente"
Precio: 25 Besitos
Tipo: Badge permanente premium
Nivel requerido: 6

Descripción Lucien:
"Pocos llevan esta marca. Indica que Lucien confía en usted.
Relativamente, por supuesto. La confianza absoluta no existe.
Pero esto es lo más cercano que ofrezco."

Efecto técnico:
- Badge permanente de nivel 5
- Emoji: 🤫
- Requisito: Nivel 6+ alcanzado
- Bonus: +10% descuento adicional en Gabinete
- Acceso a items secretos (ver sección de items ocultos)

Mensaje al comprar:
"La Marca del Confidente es suya. Bienvenido al círculo interno.
Hay cosas que solo los Confidentes pueden ver en el Gabinete.
Explore."
```

### dist_006: Corona del Guardián
```
Nombre: "Corona del Guardián"
Precio: 50 Besitos
Tipo: Badge máximo
Nivel requerido: 7

Descripción Lucien:
"El distintivo más alto del Gabinete. Solo los Guardianes de Secretos
pueden portarlo. Usted no solo conoce los secretos de Diana.
Los protege."

Efecto técnico:
- Badge permanente máximo
- Emoji: 👑
- Requisito: Nivel 7 alcanzado
- Bonus: +15% descuento en Gabinete
- Acceso a todos los items secretos
- Mención especial en narrativa

Mensaje al comprar:
"La Corona es suya, Guardián.
No hay distintivo superior a este. Ha alcanzado la cima.
Diana fue informada personalmente. Créame, eso no pasa seguido."
```

---

## Categoría: LLAVES (keys)

Desbloquean contenido narrativo oculto.

### key_001: Llave del Fragmento I
```
Nombre: "Llave del Fragmento I"
Precio: 10 Besitos
Tipo: Desbloqueo narrativo
Nivel requerido: 3

Descripción Lucien:
"Abre el primer secreto oculto. Un fragmento de historia que Diana
no cuenta públicamente. El comienzo de algo... más profundo."

Efecto técnico:
- Desbloquea fragmento narrativo secreto #1
- Permanente una vez desbloqueado
- Contenido: ~500 palabras de narrativa exclusiva

Mensaje al comprar:
"La Llave es suya. El Fragmento I está desbloqueado.
Encuéntrelo en su Historia. Está donde no estaba antes."

Contenido desbloqueado:
- Fragmento sobre el pasado de Diana
- Revela una contradicción de su personalidad
- Termina con pregunta que conecta al Fragmento II
```

### key_002: Llave del Fragmento II
```
Nombre: "Llave del Fragmento II"
Precio: 12 Besitos
Tipo: Desbloqueo narrativo
Nivel requerido: 3

Descripción Lucien:
"El segundo secreto. Más profundo que el primero.
Aquí Diana muestra algo que preferiría esconder."

Efecto técnico:
- Desbloquea fragmento narrativo secreto #2
- Requisito: Haber desbloqueado Fragmento I
- Contenido: ~600 palabras de narrativa exclusiva

Mensaje al comprar:
"La segunda Llave gira. El Fragmento II emerge.
Tenga cuidado con lo que descubre. No todo conocimiento es cómodo."
```

### key_003: Llave del Fragmento III
```
Nombre: "Llave del Fragmento III"
Precio: 15 Besitos
Tipo: Desbloqueo narrativo
Nivel requerido: 4

Descripción Lucien:
"El tercer secreto. Aquí las cosas se ponen... interesantes.
Diana no aprobó que esto estuviera disponible. Lo hice yo.
Ella no sabe. O finge no saber."

Efecto técnico:
- Desbloquea fragmento narrativo secreto #3
- Requisito: Haber desbloqueado Fragmento II
- Contenido: ~700 palabras + imagen exclusiva

Mensaje al comprar:
"Ha llegado más lejos de lo que Diana anticipó.
El Fragmento III contiene... bueno, descúbralo usted mismo.
No diga que no le advertí."
```

### key_004: Llave del Archivo Oculto
```
Nombre: "Llave del Archivo Oculto"
Precio: 20 Besitos
Tipo: Desbloqueo múltiple
Nivel requerido: 4

Descripción Lucien:
"No un fragmento. Un archivo completo. Memorias que Diana 
preferiría olvidar. O quizás no. Con ella nunca se sabe."

Efecto técnico:
- Desbloquea conjunto de 3-5 fragmentos cortos
- Contenido: Notas personales de Diana, pensamientos sueltos
- Formato: Tipo "diario" o "notas de voz transcritas"

Mensaje al comprar:
"El Archivo se abre. Lo que encontrará son retazos.
Pensamientos incompletos. Confesiones a medias.
Más reveladores, quizás, que cualquier narrativa pulida."
```

### key_005: Llave de la Primera Vez
```
Nombre: "Llave de la Primera Vez"
Precio: 18 Besitos
Tipo: Desbloqueo especial
Nivel requerido: 5

Descripción Lucien:
"La historia de cómo Diana se convirtió en Señorita Kinky.
El momento exacto. La decisión. Lo que sintió.
Esto no lo cuenta a nadie. Excepto ahora, a usted."

Efecto técnico:
- Desbloquea fragmento narrativo de origen
- Contenido: La historia del primer día de Diana como creadora
- Tono: Vulnerable, real, sin el personaje

Mensaje al comprar:
"Esta es la historia más personal del Gabinete.
Diana antes de Kinky. El momento del cambio.
Trátela con respeto."
```

---

## Categoría: RELIQUIAS (relics)

Items de alto valor, exclusivos y con efectos significativos.

### rel_001: El Primer Secreto
```
Nombre: "El Primer Secreto"
Precio: 30 Besitos
Tipo: Coleccionable + Contenido
Nivel requerido: 5

Descripción Lucien:
"Un objeto que representa el primer secreto que Diana me confió.
No el objeto literal, claro. Pero su esencia.
Ahora puede ser suyo. Con todo lo que eso implica."

Efecto técnico:
- Item coleccionable permanente en inventario
- Badge especial: "Portador del Primer Secreto" 🔮
- Desbloquea fragmento narrativo exclusivo
- +3% descuento permanente adicional

Mensaje al comprar:
"El Primer Secreto cambia de manos. 
Ahora usted es su guardián. Diana fue notificada.
Su reacción fue... interesante."
```

### rel_002: Fragmento del Espejo
```
Nombre: "Fragmento del Espejo"
Precio: 40 Besitos
Tipo: Coleccionable + Desbloqueo
Nivel requerido: 5

Descripción Lucien:
"Un pedazo del espejo donde Diana se mira antes de cada sesión.
Metafóricamente, por supuesto. O quizás no tan metafóricamente.
A través de él, verá lo que ella ve."

Efecto técnico:
- Item coleccionable permanente
- Desbloquea "Visión del Espejo": contenido behind-the-scenes
- Acceso a 3 fotos/videos del proceso creativo de Diana

Mensaje al comprar:
"El Fragmento es suyo. Cuando lo 'use', verá algo diferente.
No el resultado final. El proceso. La preparación.
Diana sin el maquillaje de la perfección."
```

### rel_003: La Carta No Enviada
```
Nombre: "La Carta No Enviada"
Precio: 50 Besitos
Tipo: Contenido único
Nivel requerido: 6

Descripción Lucien:
"Diana escribió esto hace tiempo. A alguien. No sé a quién.
Nunca lo envió. Las palabras quedaron guardadas.
Ahora usted puede leerlas. El destinatario original nunca lo hará."

Efecto técnico:
- Item coleccionable permanente
- Contenido: Carta de 500-800 palabras
- Tono: Profundamente personal, revelador
- Badge: "Lector de lo No Enviado" 💌

Mensaje al comprar:
"La Carta es suya. Léala cuando tenga tiempo para procesar.
Lo que Diana escribió aquí... no lo ha compartido con nadie más.
Ni siquiera conmigo, hasta que la encontré."
```

### rel_004: Cristal de Medianoche
```
Nombre: "Cristal de Medianoche"
Precio: 45 Besitos
Tipo: Beneficio permanente
Nivel requerido: 5

Descripción Lucien:
"Un artefacto que activa contenido especial a medianoche.
Cada noche, cuando el reloj marca las 00:00, algo se desbloquea.
Solo para quienes poseen el Cristal."

Efecto técnico:
- Item permanente
- Cada día a las 00:00 (timezone del usuario), desbloquea micro-contenido
- Puede ser: frase de Diana, pensamiento, imagen, audio corto
- Contenido rota mensualmente

Mensaje al comprar:
"El Cristal brilla a medianoche. Cada noche, algo aparece.
Solo usted lo verá. Los demás duermen sin saber lo que se pierden."
```

### rel_005: Llave Maestra del Gabinete
```
Nombre: "Llave Maestra del Gabinete"
Precio: 75 Besitos
Tipo: Desbloqueo total
Nivel requerido: 7

Descripción Lucien:
"La única Llave Maestra. Abre todo lo que está cerrado en el Gabinete.
Todos los fragmentos. Todos los archivos. Todo.
Es el objeto más valioso que poseo. Y el más peligroso."

Efecto técnico:
- Desbloquea TODOS los fragmentos narrativos secretos
- Desbloquea items futuros automáticamente (de tipo Llave)
- Badge supremo: "Portador de la Llave Maestra" 🗝️
- Descuento permanente +20%

Mensaje al comprar:
"No hay nada más allá de esto. 
La Llave Maestra abre cada puerta del Gabinete.
Pasadas, presentes y futuras.
Use este poder con... bueno, como quiera usarlo. Ya no puedo detenerlo."
```

---

## ITEMS OCULTOS (Solo visibles con Marca del Confidente o superior)

### secret_001: Susurro de Lucien
```
Nombre: "Susurro de Lucien"
Precio: 20 Besitos
Tipo: Contenido exclusivo
Nivel requerido: 6
Visibilidad: Solo Confidentes+

Descripción Lucien:
"No todo es sobre Diana. A veces, incluso yo tengo algo que decir.
Este es mi susurro. Mi perspectiva. Lo que observo y no comento.
Hasta ahora."

Efecto técnico:
- Audio de "Lucien" (puede ser texto estilizado si no hay audio)
- Contenido: La perspectiva de Lucien sobre los usuarios, Diana, el sistema
- Tono: Meta, rompe un poco la cuarta pared

Mensaje al comprar:
"Esto es... inusual. Normalmente no hablo de mí mismo.
Pero usted ha llegado lejos. Merece escuchar lo que pienso.
No se lo cuente a Diana."
```

### secret_002: Coordenadas
```
Nombre: "Las Coordenadas"
Precio: 35 Besitos
Tipo: Easter egg
Nivel requerido: 6
Visibilidad: Solo Confidentes+

Descripción Lucien:
"Números. Solo números. No diré qué significan.
Quizás nada. Quizás todo. 
Los exploradores verdaderos encontrarán su significado."

Efecto técnico:
- Revela coordenadas crípticas
- Pueden ser: fecha importante, código para contenido, referencia externa
- Diseñado para que usuarios investiguen

Mensaje al comprar:
"Aquí están. Qué hace con ellas es su decisión.
No espere ayuda. Este acertijo es suyo solo."
```

---

# F4.2: FLUJOS DE USUARIO

## Flujo: Entrar al Gabinete

```
[Usuario toca "El Gabinete" en menú]

[Mensaje de bienvenida - primera vez]
"Bienvenido a mi Gabinete.

Este es mi espacio personal. Aquí guardo objetos que Diana ha
autorizado para intercambio. Algunos valiosos. Otros... menos.

Sus Besitos disponibles: {total}
Su nivel actual: {nivel} ({nombre_nivel})

Cada categoría tiene su propósito. Explore. Pero no espere
que le venda cualquier cosa. Algunos items requieren... mérito."

[BOTONES - Categorías]
[⚡ Efímeros]
[🎖️ Distintivos]  
[🔑 Llaves]
[💎 Reliquias]
[📦 Mi Inventario]
[🔙 Volver]
```

```
[Mensaje de bienvenida - visitas posteriores]
"De vuelta en el Gabinete.

Besitos: {total}
{Si hay items nuevos: "Hay {n} items nuevos desde su última visita."}
{Si tiene items en inventario sin usar: "Tiene {n} items sin utilizar."}

¿Qué busca hoy?"

[BOTONES - Categorías]
```

## Flujo: Ver categoría

```
[Usuario toca "⚡ Efímeros"]

"Efímeros. Placeres de un solo uso.
{descripción_categoría}

Sus Besitos: {total}"

[Lista de items]
━━━━━━━━━━━━━━━━━━━━━━━

⚡ Sello del Día
{precio} Favor(es)
[Ver detalles]

━━━━━━━━━━━━━━━━━━━━━━━

⚡ Susurro Efímero  
{precio} Besitos
[Ver detalles]

━━━━━━━━━━━━━━━━━━━━━━━

{Si hay item que no puede comprar por nivel:}
🔒 Vistazo al Sensorium
Requiere nivel {n} ({nombre})
[Ver requisitos]

━━━━━━━━━━━━━━━━━━━━━━━

[🔙 Volver al Gabinete]
```

## Flujo: Ver detalle de item

```
[Usuario toca "Ver detalles" en Susurro Efímero]

━━━━━━━━━━━━━━━━━━━━━━━
⚡ SUSURRO EFÍMERO
━━━━━━━━━━━━━━━━━━━━━━━

Precio: 3 Besitos
Sus Besitos: {total}
{Si tiene descuento: "Precio con descuento: {precio_descuento} Besitos"}

━━━━━━━━━━━━━━━━━━━━━━━

"{descripción_de_lucien}"

━━━━━━━━━━━━━━━━━━━━━━━

Tipo: Contenido único
Duración: Una reproducción

━━━━━━━━━━━━━━━━━━━━━━━

{Si puede comprar:}
[Adquirir] [🔙 Volver]

{Si no tiene suficientes Besitos:}
Le faltan {diferencia} Besitos.
[Ver cómo ganar Besitos] [🔙 Volver]

{Si no tiene nivel suficiente:}
Requiere nivel {n} ({nombre}).
Usted es nivel {actual}.
[🔙 Volver]
```

## Flujo: Proceso de compra

```
[Usuario toca "Adquirir"]

[Paso 1: Confirmación]
"¿Confirma la adquisición?

Item: {nombre}
Precio: {precio} Favor(es)
{Si tiene descuento: "Descuento aplicado: {porcentaje}%"}

Después de esta transacción:
Besitos restantes: {total - precio}"

[Confirmar] [Cancelar]
```

```
[Paso 2A: Compra exitosa]

"Transacción completada.

'{nombre}' ha sido añadido a su inventario.

{mensaje_post_compra_específico_del_item}

Besitos restantes: {nuevo_total}"

[Usar ahora] [Ver inventario] [Seguir explorando]
```

```
[Paso 2B: Error - Besitos insuficientes]
(No debería pasar si UI está bien, pero por seguridad)

"La transacción no puede completarse.

Sus Besitos cambiaron desde que vio el precio.
Actual: {total} | Necesario: {precio}

Esto es... incómodo. Intente de nuevo."

[🔙 Volver]
```

## Flujo: Ver inventario

```
[Usuario toca "Mi Inventario"]

"Su inventario personal.

Aquí están los objetos que ha adquirido del Gabinete."

━━━━━━━━━━━━━━━━━━━━━━━
📦 ITEMS ACTIVOS
━━━━━━━━━━━━━━━━━━━━━━━

{Items que puede usar}

⚡ Susurro Efímero (x1)
    Adquirido: {fecha}
    [Usar]

🔑 Llave del Fragmento I (Usado ✓)
    Contenido desbloqueado

━━━━━━━━━━━━━━━━━━━━━━━
🎖️ DISTINTIVOS
━━━━━━━━━━━━━━━━━━━━━━━

👁️ Sello del Visitante
🔍 Insignia del Observador

━━━━━━━━━━━━━━━━━━━━━━━
💎 COLECCIONABLES
━━━━━━━━━━━━━━━━━━━━━━━

🔮 El Primer Secreto
    Contenido asociado: [Ver]

━━━━━━━━━━━━━━━━━━━━━━━

[🔙 Volver al Gabinete]
```

## Flujo: Usar item consumible

```
[Usuario toca "Usar" en Susurro Efímero]

"Está a punto de usar: Susurro Efímero

⚠️ Este item se consume al usarse.
Una vez activado, no puede recuperarse.

{Si es audio: "Asegúrese de tener audio activado."}
{Si es contenido temporal: "El contenido estará disponible por {tiempo}."}

¿Continuar?"

[Usar ahora] [Guardar para después]
```

```
[Después de usar]

{El contenido se muestra}

"El Susurro ha sido consumido.

{mensaje_post_uso}

[🔙 Volver al inventario]"
```

---

# F4.3: SISTEMA DE DESCUENTOS

## Descuentos por nivel

| Nivel | Descuento base |
|-------|---------------|
| 1-3 | 0% |
| 4 | 5% |
| 5 | 10% |
| 6 | 15% |
| 7 | 20% |

## Descuentos por distintivos

| Distintivo | Descuento adicional |
|------------|---------------------|
| Emblema del Reconocido | +5% |
| Marca del Confidente | +10% |
| Corona del Guardián | +15% |

## Descuentos por reliquias

| Reliquia | Descuento adicional |
|----------|---------------------|
| El Primer Secreto | +3% |
| Llave Maestra | +20% |

## Cálculo de descuento total

```
descuento_total = min(
    descuento_nivel + 
    descuento_distintivos + 
    descuento_reliquias,
    50  # Máximo 50% de descuento
)

precio_final = precio_base * (1 - descuento_total/100)
precio_final = round(precio_final, 1)  # Redondear a 1 decimal
```

## Mostrar descuentos

Cuando usuario tiene descuento:
```
"Precio: ~~{precio_original}~~ → {precio_final} Besitos
Descuento nivel {n}: {x}%
{Si tiene distintivo: "Bonus {distintivo}: +{y}%"}
Total: {descuento_total}% de descuento"
```

---

# F4.4: ITEMS LIMITADOS Y TEMPORALES

## Sistema de stock limitado

Algunos items pueden tener stock limitado:

```
ShopItem (campos adicionales):
    is_limited: bool = False
    total_stock: int | null  # null = ilimitado
    remaining_stock: int | null
    limit_per_user: int = 1  # Máximo por usuario
```

## Mostrar item limitado

```
"⚡ Edición Especial - Susurro de Año Nuevo
Precio: 10 Besitos

⚠️ EDICIÓN LIMITADA
Disponibles: {remaining}/{total}
Límite por persona: 1

{descripción}

[Adquirir]"
```

## Sistema de items temporales (eventos)

```
ShopItem (campos adicionales):
    available_from: datetime | null
    available_until: datetime | null
    event_name: str | null
```

## Mostrar item temporal

```
"🎃 Confesión de Halloween
Precio: 12 Besitos

⏰ DISPONIBLE POR TIEMPO LIMITADO
Termina en: {tiempo_restante}

{descripción}

[Adquirir]"
```

---

# F4.5: RECOMENDACIONES PERSONALIZADAS

## Basadas en arquetipo

Al entrar al Gabinete, mostrar recomendación según arquetipo:

| Arquetipo | Recomendación |⁸
|-----------|---------------|
| EXPLORER | Llaves (contenido oculto) |
| DIRECT | Efímeros (uso inmediato) |
| ROMANTIC | Reliquias emotivas (Carta No Enviada) |
| ANALYTICAL | Items con más "información" |
| PERSISTENT | Distintivos (reconocimiento) |
| PATIENT | Reliquias de largo plazo |

## Mensaje de recomendación

```
"Basándome en lo que he observado de usted...

Quizás le interese: {item_recomendado}
{razón_breve}

Pero explore como prefiera. Solo es... una sugerencia."
```

## Basadas en historial

- Si ha comprado todas las Llaves: sugerir Llave Maestra
- Si tiene muchos Efímeros sin usar: recordar inventario
- Si está cerca de un nivel nuevo: mencionar items de ese nivel

---

# F4.6: NOTIFICACIONES DEL GABINETE

Integrar en el  servicios actual de notificaciones
## Item nuevo disponible

```
"El Gabinete tiene algo nuevo.

'{nombre_item}' ha sido añadido a la colección.
{descripción_corta}

Precio: {precio} Besitos

¿Desea verlo?"

[Ver item] [Ahora no]
```

## Item limitado casi agotado

```
"Aviso del Gabinete:

'{nombre_item}' está casi agotado.
Quedan solo {remaining} unidades.

Si lo deseaba... el momento es ahora."

[Ver item] [Ignorar]
```

## Item temporal por terminar

```
"Recordatorio del Gabinete:

'{nombre_item}' dejará de estar disponible en {tiempo}.

Es la última oportunidad."

[Ver item]
```

---

# F4.7: COMANDOS DE ADMIN

## Gestión de items
Verificar si ya existen estos comandos o en caso de que sean nuevos integrarlos completamente al menú de administración generando sus botones del teclado para el menú callback y todo lo necesario

```
/admin_shop_add
    Wizard para agregar nuevo item:
    1. Categoría
    2. Nombre
    3. Precio
    4. Descripción
    5. Nivel requerido
    6. Tipo (consumible, permanente, etc.)
    7. Límites (si aplica)

/admin_shop_edit <item_id>
    Editar item existente

/admin_shop_disable <item_id>
    Desactivar item (no eliminar)

/admin_shop_stock <item_id> <cantidad>
    Ajustar stock de item limitado
```

## Estadísticas

```
/admin_shop_stats

Muestra:
- Items más vendidos (últimos 30 días)
- Ingresos totales en Besitos
- Categoría más popular
- Items sin ventas
- Usuarios con más compras
```

## Promociones

```
/admin_shop_promo <item_id> <descuento%> <duración_horas>

Crea promoción temporal para un item.
Notifica a usuarios relevantes.
```

---

# CRITERIOS DE ACEPTACIÓN FASE 4

## Catálogo
- [ ] Mínimo 20 items creados y cargados
- [ ] 4 categorías funcionando
- [ ] Descripciones de Lucien para cada item
- [ ] Niveles de acceso implementados

## Flujos de usuario
- [ ] Navegación por categorías funciona
- [ ] Vista de detalle de item completa
- [ ] Proceso de compra con confirmación
- [ ] Inventario muestra items comprados
- [ ] Uso de items consumibles funciona

## Descuentos
- [ ] Descuento por nivel aplicado correctamente
- [ ] Descuento por distintivos funciona
- [ ] Descuento máximo limitado a 50%
- [ ] UI muestra precio original y final

## Items especiales
- [ ] Items limitados muestran stock
- [ ] Items temporales muestran tiempo restante
- [ ] Items ocultos solo visibles para Confidentes+

## Personalización
- [ ] Recomendaciones por arquetipo funcionan
- [ ] Historial afecta sugerencias

## Notificaciones
- [ ] Notificación de item nuevo
- [ ] Alerta de stock bajo
- [ ] Recordatorio de tiempo limitado

## Admin
- [ ] CRUD de items funciona
- [ ] Estadísticas disponibles

---

# NOTAS DE IMPLEMENTACIÓN

1. **Transacciones:** Compras deben ser atómicas (descontar Besitos y agregar item en una transacción)
2. **Cache:** Cachear catálogo, invalidar al modificar
3. **Imágenes:** Items pueden tener imagen opcional (URL)
4. **Contenido:** Items tipo "Llave" deben vincular a fragmentos narrativos de Fase 5
5. **Auditoría:** Log de todas las compras para análisis

---

# ARCHIVOS DE REFERENCIA

- Fase 0: Definición inicial de items
- Fase 2: Sistema de Besitos (spend_favors)
- Fase 3: Arquetipos para recomendaciones
- `bot/shop/` - Módulo existente de tienda

---

*Documento generado para implementación por Claude Code*
*Proyecto: El Mayordomo del Diván*
*Fase: 4 - El Gabinete*
	
