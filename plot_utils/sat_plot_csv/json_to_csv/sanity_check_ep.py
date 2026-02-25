import pandas as pd
import json

# ----- Script per fare check delle colonne dopo il aver trasformato il "evaluations.json" in un csv -----

input_csv = 'estratto_evaluations.csv'
output_check = 'sanity_check_step.csv'

def sanity_check_by_steps():
    try:
        df = pd.read_csv(input_csv)
        check_results = []

        # Colonne che contengono dati registrati per ogni step
        colonne_per_step = [
            'hist_stats/current_time',
            'hist_stats/step_reward',
            'hist_stats/current_sat',
            'hist_stats/total_distance'
        ]

        for index, row in df.iterrows():
            counts = {'riga_csv': index + 1}
            
            # Calcola la somma dei passi (step) da episode_lengths
            try:
                # Trasforma la stringa in episode_lengths eg."[32, 17, 360]" in lista e sommiamo i valori
                # Per avere la lunghezza dell'iterazione a grana degli step
                lengths_list = json.loads(row['hist_stats/episode_lengths'])
                totale_step_attesi = sum(lengths_list)
            except:
                totale_step_attesi = 0
            
            counts['step_totali_attesi'] = totale_step_attesi

            # Conta gli elementi nelle colonne per step e fa confronto
            discrepanze = []
            for col in colonne_per_step:
                try:
                    valori = json.loads(row[col])
                    conteggio_effettivo = len(valori)
                except:
                    conteggio_effettivo = 0
                
                counts[f"{col}_count"] = conteggio_effettivo
                
                # Check, conteggio deve essere uguale alla somma di episode_lengths
                if conteggio_effettivo != totale_step_attesi:
                    discrepanze.append(f"{col}({conteggio_effettivo})")

            # Stato della riga
            if totale_step_attesi == 0:
                counts['STATO'] = "VUOTO o Errore in episode_lengths"
            elif not discrepanze:
                counts['STATO'] = "OK (Coerente)"
            else:
                counts['STATO'] = f"ANOMALIA: {', '.join(discrepanze)} vs Sum={totale_step_attesi}"
            
            check_results.append(counts)

        # Creazione del report finale
        df_check = pd.DataFrame(check_results)
        df_check.to_csv(output_check, index=False)
        
        print(f"Sanity check completato! Report salvato in: '{output_check}'.")
        
        
        errori = df_check[df_check['STATO'].str.contains("ANOMALIA")]
        if not errori.empty:
            print(f"\n  Rilevate {len(errori)} righe incoerenti!")
            print(errori[['riga_csv', 'STATO']].to_string(index=False))
        else:
            print("\n OK! Il numero di step in ogni colonna coincide con la somma di episode_lengths.")

    except Exception as e:
        print(f"Errore durante l'esecuzione: {e}")

if __name__ == "__main__":
    sanity_check_by_steps()