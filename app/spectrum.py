from collections import defaultdict


QUESTION_MAP = [
    {"A": "UD", "B": "D", "C": "C", "D": "I", "E": "UI"},
    {"A": "UD", "B": "D", "C": "C", "D": "I", "E": "UI"},
    {"A": "UD", "B": "D", "C": "C", "D": "I", "E": "UI"},
    {"A": "UD", "B": "D", "C": "C", "D": "I", "E": "UI"},
    {"A": "UD", "B": "D", "C": "C", "D": "I", "E": "UI"},
    {"A": "UD", "B": "D", "C": "C", "D": "I", "E": "UI"},
    {"A": "UD", "B": "D", "C": "C", "D": "I", "E": "UI"},
    {"A": "UD", "B": "D", "C": "C", "D": "I", "E": "UI"},
    {"A": "UD", "B": "D", "C": "C", "D": "I", "E": "UI"},
    {"A": "UD", "B": "D", "C": "C", "D": "I", "E": "UI"},
]


QUESTIONS = [
    {
        "id": 1,
        "text": "Frente a la seguridad en Colombia, que posicion se acerca mas a lo que piensas?",
        "options": {
            "A": "Mano dura sin tanta contemplacion.",
            "B": "Autoridad fuerte, pero dentro de la ley.",
            "C": "Seguridad con equilibrio entre control y derechos.",
            "D": "Seguridad atacando tambien causas sociales.",
            "E": "Cambios profundos al modelo policial y de justicia.",
        },
    },
    {
        "id": 2,
        "text": "Sobre el papel del Estado en la economia, que prefieres?",
        "options": {
            "A": "Reducirlo al minimo y dejar que mande el mercado.",
            "B": "Menos trabas para empresas y emprendedores.",
            "C": "Estado y mercado trabajando con equilibrio.",
            "D": "Estado fuerte para corregir desigualdades.",
            "E": "Transformar de fondo el modelo economico.",
        },
    },
    {
        "id": 3,
        "text": "Sobre la explotacion de recursos naturales (petroleo, carbon y mineria) en Colombia, piensas que:",
        "options": {
            "A": "Debe impulsarse al maximo y sin tantas trabas ambientales; es la principal fuente de ingresos del pais.",
            "B": "Debe continuar bajo reglas estables que den confianza a la inversion extranjera, planificando una transicion muy gradual.",
            "C": "Se debe buscar un equilibrio que mantenga los ingresos de la mineria pero aplicando controles ambientales estrictos.",
            "D": "Hay que reducir gradualmente la dependencia del petroleo y carbon, priorizando la conservacion del agua y las energias limpias.",
            "E": "Se debe detener de inmediato toda nueva exploracion de combustibles fosiles para transitar a un modelo economico agricola y verde.",
        },
    },
    {
        "id": 4,
        "text": "Sobre impuestos, cual idea te representa mas?",
        "options": {
            "A": "El Estado cobra demasiado y gasta mal.",
            "B": "Bajar impuestos para mover la economia.",
            "C": "Cobrar lo necesario y vigilar bien el gasto.",
            "D": "Que paguen mas quienes mas tienen.",
            "E": "Redistribucion fuerte de riqueza y privilegios.",
        },
    },
    {
        "id": 5,
        "text": "En temas de orden publico y protesta social, que pesa mas para ti?",
        "options": {
            "A": "Restablecer el orden rapidamente.",
            "B": "Permitir protesta, pero sin bloquear al pais.",
            "C": "Proteger protesta y movilidad con balance.",
            "D": "Escuchar las causas antes de reprimir.",
            "E": "La protesta es una herramienta legitima de cambio profundo.",
        },
    },
    {
        "id": 6,
        "text": "Sobre valores, familia y costumbres, tu postura se parece mas a:",
        "options": {
            "A": "Defender valores tradicionales con firmeza.",
            "B": "Conservar tradiciones importantes sin imponer todo.",
            "C": "Respetar distintas formas de vida.",
            "D": "Ampliar derechos y reducir discriminacion.",
            "E": "Cambiar estructuras culturales que reproducen desigualdad.",
        },
    },
    {
        "id": 7,
        "text": "Si hay conflicto entre crecimiento economico y proteccion social, eliges:",
        "options": {
            "A": "Crecimiento primero; lo demas llega despues.",
            "B": "Crecimiento con reglas claras.",
            "C": "Un punto medio sostenible.",
            "D": "Proteccion social como prioridad.",
            "E": "Replantear el modelo de crecimiento.",
        },
    },
    {
        "id": 8,
        "text": "Frente a los grupos armados ilegales y la violencia en las regiones, cual debe ser la prioridad del gobierno?",
        "options": {
            "A": "Confrontacion y sometimiento militar absoluto, sin concesiones de beneficios ni negociaciones politicas.",
            "B": "Ofensiva militar fuerte de las Fuerzas Armadas, y dialogar solo si hay un cese al fuego verificable y entrega de armas.",
            "C": "Buscar salidas negociadas condicionadas, combinando la presion militar con el cumplimiento de los acuerdos de paz previos.",
            "D": "Priorizar el dialogo politico, la implementacion del Acuerdo de Paz y la inversion social directa en las zonas mas afectadas.",
            "E": "Atacar las causas estructurales de la violencia resolviendo de raiz la propiedad de la tierra y desmantelando los monopolios economicos.",
        },
    },
    {
        "id": 9,
        "text": "Sobre los partidos politicos tradicionales, piensas que:",
        "options": {
            "A": "Al menos sostienen el orden institucional.",
            "B": "Hay que renovarlos, pero no destruirlos.",
            "C": "Sirven si hacen acuerdos utiles.",
            "D": "Han protegido demasiados privilegios.",
            "E": "Son parte central del problema estructural.",
        },
    },
    {
        "id": 10,
        "text": "Antes de votar, que pesa mas en tu decision?",
        "options": {
            "A": "Seguridad, autoridad y defensa del orden.",
            "B": "Economia, estabilidad y confianza.",
            "C": "Equilibrio, propuestas viables y moderacion.",
            "D": "Derechos, igualdad y politicas sociales.",
            "E": "Ruptura con el modelo actual.",
        },
    },
]

LABELS = {
    "UD": "Ultraderecha",
    "D": "Derecha",
    "C": "Centro",
    "I": "Izquierda",
    "UI": "Ultraizquierda",
}

PROFILE_SUMMARIES = {
    "UD": (
        "Eres un defensor firme de la ley, el orden y la propiedad privada. Para ti, el país "
        "no está para experimentos ni paños tibios: la seguridad de mano dura es la base de todo. "
        "Esta categoría incluye tanto al conservadurismo tradicional como a las corrientes libertarias "
        "que exigen la mínima intervención del Estado en la economía y la reducción drástica de impuestos."
    ),
    "D": (
        "Crees en el orden, la estabilidad y la libre empresa como los motores del progreso. "
        "Apoyas que la autoridad se haga sentir dentro del marco de la ley y prefieres reformas "
        "graduales. Valoras la estabilidad institucional y la confianza inversionista antes que "
        "los giros drásticos en las políticas del país."
    ),
    "C": (
        "Huyes de los dogmas y los discursos extremos. Para ti, el país se construye con soluciones "
        "prácticas, no con camisetas ideológicas. Puedes estar de acuerdo con la seguridad fuerte "
        "pero también con la protección social, evaluando cada problema con cabeza fría y sensatez."
    ),
    "I": (
        "Tu prioridad es reducir la brecha social y garantizar oportunidades para todos. "
        "Tus respuestas se alinean estrechamente con el progresismo moderno y la socialdemocracia: "
        "apoyas la intervención activa del Estado en salud y pensiones, defiendes la ampliación de "
        "derechos civiles y consideras la justicia ambiental como pilar central del progreso."
    ),
    "UI": (
        "Buscas un cambio profundo y estructural en el modelo económico y social. Para ti, las reformas "
        "moderadas no son suficientes porque el sistema actual reproduce privilegios. Apoyas la movilización "
        "y la redistribución activa de la riqueza para lograr justicia social."
    ),
    "MIXED": (
        "Tu pensamiento es pragmático y no cabe en moldes ideológicos clásicos. Tienes una mezcla muy colombiana: "
        "puedes exigir orden y seguridad en algunos temas, pero reclamar un rol fuerte del Estado en lo social. "
        "También suele reflejar una fuerte postura antipolítica o de desconfianza transversal hacia el establecimiento tradicional."
    ),
}

SELF_LABELS_ES = {
    "UD": "Ultraderecha",
    "D": "Derecha",
    "C": "Centro",
    "I": "Izquierda",
    "UI": "Ultraizquierda",
    "NONE": "Ninguna",
}


def build_share_text(label: str, percentages: dict) -> str:
    return (
        f"Hice el Test Spectrum Colombia y salí {label}.\n"
        f"UD {percentages['UD']}% | D {percentages['D']}% | C {percentages['C']}% | "
        f"I {percentages['I']}% | UI {percentages['UI']}%\n"
        "Hazlo y descubre si estás en la etiqueta que defiendes."
    )


def calculate_spectrum(answers: list[str], self_label: str = "NONE") -> dict:
    scores = defaultdict(int)

    for index, answer in enumerate(answers):
        axis = QUESTION_MAP[index][answer]
        scores[axis] += 1

    total = len(answers)
    percentages = {
        axis: round(scores[axis] / total * 100, 2)
        for axis in ["UD", "D", "C", "I", "UI"]
    }
    highest = max(percentages.values())
    dominant_axes = [axis for axis, value in percentages.items() if value == highest]

    if len(dominant_axes) > 1:
        dominant_axis = "MIXED"
        dominant_label = "Mixto"
    else:
        dominant_axis = dominant_axes[0]
        dominant_label = LABELS[dominant_axis]

    # Calcular feedback del "Efecto Espejo"
    self_label_es = SELF_LABELS_ES.get(self_label, "Ninguna")
    if self_label == "NONE":
        mirror_feedback = (
            f"El test revela que tu pensamiento se alinea principalmente con la **{dominant_label}**."
        )
    elif self_label == dominant_axis:
        mirror_feedback = (
            f"¡Total coherencia! Te consideras de **{self_label_es}** y tus respuestas a temas "
            "prácticos lo confirman al 100%. Tienes muy claras tus prioridades políticas."
        )
    else:
        mirror_feedback = (
            f"¡Aquí está la sorpresa! Te identificas como de **{self_label_es}**, pero tus respuestas "
            f"reales sobre economía, orden y derechos te ubican más cerca de la **{dominant_label}**. "
            "Esto demuestra que tus convicciones reales van más allá de las etiquetas habituales."
        )

    return {
        "percentages": percentages,
        "dominant_axis": dominant_axis,
        "dominant": dominant_label,
        "summary": PROFILE_SUMMARIES[dominant_axis],
        "mirror_feedback": mirror_feedback,
        "share_text": build_share_text(dominant_label, percentages),
    }

