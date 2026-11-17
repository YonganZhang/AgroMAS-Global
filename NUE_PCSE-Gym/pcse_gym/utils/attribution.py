"""Read-only explanations: formatter receives a deep copy; actions are never returned to env."""
import copy

def explain_decision(observation, latent, proposed_action, executed_action, reasons, formatter=None):
    record = dict(observation=copy.deepcopy(observation), inferred_latent=copy.deepcopy(latent),
                  proposed_action=float(proposed_action), executed_action=float(executed_action),
                  proposed_kg_N_ha=float(proposed_action)*10, executed_kg_N_ha=float(executed_action)*10,
                  filter_reasons=list(reasons), inference_inputs="observable crop and past weather only")
    record['explanation'] = (f"Proposed {proposed_action*10:g} kg N/ha; executed {executed_action*10:g} kg N/ha. " +
        ("Filtered by " + ", ".join(reasons) + "." if reasons else "Passed configured agronomic constraints."))
    if formatter is not None:
        record['optional_formatted_text'] = str(formatter(copy.deepcopy(record)))
    return record
