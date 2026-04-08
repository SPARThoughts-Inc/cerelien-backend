from agents import RunContextWrapper, function_tool

from app.domain.business_process.agents.context import ConsultationContext


@function_tool
async def get_patient_profile(ctx: RunContextWrapper[ConsultationContext]) -> str:
    """Retrieve the patient's demographic profile including name, diabetes type, and contact info."""
    patient_workflow = ctx.context.patient_workflow
    patient_id = int(ctx.context.patient_id)
    patient = await patient_workflow.get_patient(patient_id)
    return (
        f"Patient: {patient.first_name} {patient.last_name}\n"
        f"Diabetes Type: {patient.diabetes_type or 'Unknown'}\n"
        f"Date of Birth: {patient.date_of_birth or 'Unknown'}\n"
        f"Email: {patient.email or 'Not provided'}\n"
        f"Phone: {patient.phone_number or 'Not provided'}"
    )


@function_tool
async def get_patient_glucose_data(ctx: RunContextWrapper[ConsultationContext], days: int = 30) -> str:
    """Retrieve the patient's glucose readings for a specified number of days. Returns A1C, average, min, max, and time-in-range summary."""
    patient_workflow = ctx.context.patient_workflow
    patient_id = int(ctx.context.patient_id)

    readings = await patient_workflow.get_glucose_readings(patient_id, days=days)
    if not readings:
        return "No glucose readings found for the specified period."

    # Separate A1C and CGM readings
    a1c_readings = [r for r in readings if r.reading_type == "a1c"]
    glucose_readings = [r for r in readings if r.reading_type != "a1c"]

    lines = []

    if a1c_readings:
        latest_a1c = a1c_readings[0].value
        lines.append(f"Latest A1C: {latest_a1c}%")

    if glucose_readings:
        values = [float(r.value) for r in glucose_readings]
        avg_val = sum(values) / len(values)
        min_val = min(values)
        max_val = max(values)
        in_range = sum(1 for v in values if 70 <= v <= 180)
        time_in_range = (in_range / len(values)) * 100

        lines.append(f"Average Glucose: {avg_val:.1f} mg/dL")
        lines.append(f"Min: {min_val:.1f} mg/dL")
        lines.append(f"Max: {max_val:.1f} mg/dL")
        lines.append(f"Time in Range (70-180): {time_in_range:.1f}%")
        lines.append(f"Total Readings: {len(glucose_readings)} over {days} days")

    return "\n".join(lines) if lines else "No glucose data available."


@function_tool
async def get_analytics_results(ctx: RunContextWrapper[ConsultationContext]) -> str:
    """Retrieve analytics results for the patient including trends and risk assessments."""
    patient_workflow = ctx.context.patient_workflow
    patient_id = int(ctx.context.patient_id)

    result = await patient_workflow.get_analytics(patient_id)
    if not result:
        return "No analytics results available."

    lines = []
    if result.risk_score:
        lines.append("Risk Score:")
        for key, value in result.risk_score.items():
            lines.append(f"  {key}: {value}")
    if result.trend:
        lines.append("Trend:")
        for key, value in result.trend.items():
            lines.append(f"  {key}: {value}")
    if result.complication_flags:
        lines.append("Complication Flags:")
        for flag in result.complication_flags:
            lines.append(f"  - {flag}")

    return "\n".join(lines) if lines else "No analytics data available."


@function_tool
async def get_medications(ctx: RunContextWrapper[ConsultationContext]) -> str:
    """Retrieve the patient's current medication list with dosage, frequency, and adherence rates."""
    patient_workflow = ctx.context.patient_workflow
    patient_id = int(ctx.context.patient_id)

    meds = await patient_workflow.get_medications(patient_id)
    if not meds:
        return "No medications on record."

    lines = []
    for med in meds:
        adherence = f"{float(med.adherence_rate) * 100:.0f}%" if med.adherence_rate is not None else "N/A"
        lines.append(
            f"- {med.name}: {med.dosage or 'N/A'} | {med.frequency or 'N/A'} | Adherence: {adherence}"
        )

    return "\n".join(lines)
