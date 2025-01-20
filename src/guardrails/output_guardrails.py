def financial_advise_guardrails(model_output):
    if("I cannot help with financial advice" in model_output["answer"]):
        model_output["context"] = []
    return model_output