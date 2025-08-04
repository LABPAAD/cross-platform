import os
import openai
import pandas as pd
import time
import csv
import requests
import datetime

wait_time = 30

def configurar_api():
    openai.api_key = "api_key"

def ler_dataset(file_name):
    df = pd.read_csv(file_name, sep="\t", encoding="utf-8")
    return df

def avaliar_comentario(comentario):
    try:
        print("Fazendo requisições...")
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
            {
                "role": "system",
                "content": """You are an evaluator of comment stances in English in the context of police operations. Comments should be evaluated as approve, disapprove, or neutral. Before making the evaluation, be sure to whom the comment is addressed (some comments disapprove of the opinion of others who disagree with the police action, which makes the comment one of approval).
                Comments may contain sarcasm, slang, figurative language, and typos. The comment is considered neutral when it neither approves nor disapproves or is not in the context of the police operation. Respond only with 0, -1, or 1.""",
            },
            {
                "role": "user",
                "content": f"""Suppose you have to describe the stance from the provided list that is evoked after reading the text about the police action by most people. Which would you select? Map your answer with none: 0, against: -1, in favor: 1. Do not explain.
                Text: {comentario}. Possible stances: none, against, in favor""",
            },
            ],
            temperature=0.2,
            timeout=10,
        )
    except openai.error.ServiceUnavailableError:
        print(
            "The server is overloaded or not ready yet, retrying in 5 seconds."
        )
        time.sleep(5)
        return None
    except requests.exceptions.ReadTimeout:
        print("\nThe request timed out.\n")
        time.sleep(5)
        return None
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)
        return None
    return response["choices"][0]["message"]["content"]


def salvar_resultado(id_comentario, comentario, rotulo_manual, posicao, new_file):
    arquivo_existe = os.path.isfile(new_file)

    with open(new_file, mode="a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.writer(arquivo, delimiter="\t")
        if not arquivo_existe or os.stat(new_file).st_size == 0:
            escritor.writerow(["id_comentario", "comentario", "rotulo_manual", "posicao_gpt"])
        escritor.writerow([id_comentario, comentario, rotulo_manual, posicao])


def main(file_name, new_file):
    configurar_api()
    df = ler_dataset(file_name)

    while not df.empty:
        row = df.iloc[-1]
        id_comment = row.id_comentario
        comentario = row.comentario
        # rotulo_manual = row.posicionamento
        rotulo_manual = "x"

        print(datetime.datetime.now())
        print(f"faltam {len(df)} comentarios.\n")

        print(f"Avaliando o comentário: {comentario}")
        posicao = avaliar_comentario(comentario)
        if posicao is not None:
            print(f"O posicionamento para o comentário foi: {posicao}")
            salvar_resultado(id_comment, comentario, rotulo_manual, posicao, new_file)
            df = df.iloc[:-1]
            df.to_csv(file_name, index=False, sep="\t")
            time.sleep(3)

    print("All comments have been evaluated!")


if __name__ == "__main__":
    #make a copy of the file to avoid overwriting
    file_name = "arquive_to_process_copy.csv"
    new_file = "result.csv"
    main(file_name, new_file)
