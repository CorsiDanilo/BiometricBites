from tqdm import tqdm
import numpy as np

def compute_similarities(template_list, similarity_function: callable):
    all_similarities = []
    genuine_claims = 0
    impostor_claims = 0
    for i, (label_i, template_i) in enumerate(tqdm(template_list, desc="Compute similarities")): #for every row (probe)
        row_similarities = []
        for j, (label_j, template_j) in enumerate(template_list): #for every column (template)
            if i != j: #Do not consider main diagonal elements
                if label_i == label_j: #We have to compare the identities to template_list must be some labels..
                    genuine_claims += 1
                else:
                    impostor_claims += 1
            similarity = similarity_function(template_i, template_j)
            row_similarities.append((label_j, similarity)) #Add the tuple (similarity_with_who, similarity_value) to the row
        all_similarities.append(row_similarities)
    return genuine_claims, impostor_claims, all_similarities

#OpenSet Identification Multiple Template
def open_set_identification_eval(template_list, threshold, genuine_claims=None, impostor_claims=None, all_similarities=None): 
    if genuine_claims is None or impostor_claims is None or all_similarities is None:
        genuine_claims, impostor_claims, all_similarities = compute_similarities(template_list)
    DI = [0 for _ in range(len(template_list))] #Detection and Identification
    GR = FA = 0
    for i, (label_i, template_i) in enumerate(template_list): #for every row (probe)
        best_match_label, first_similarity = all_similarities[i][0] #L_i,1, the most similar template
        if first_similarity >= threshold:
            if label_i == best_match_label: #the identity!! (to change)
                DI[0] += 1
                for j, (label_j, template_j) in enumerate(template_list): #Parallel impostor case: jump the templates belonging to label(i) since i not in G
                    k = None
                    if i != j: #Do not consider main diagonal elements so the case in which the template is compared to itself
                        if (k == None) and (label_i != label_j) and all_similarities[i][j][1] >= threshold: #The first template != label(i) has a similarity >= t
                            k = j
                    if k != None:
                        FA += 1
                    else:
                        GR += 1
            else:
                for j, (label_j, template_j) in enumerate(template_list): #If genuine yet not the first, look for higher ranks
                    k = None
                    if i != j: #Do not consider main diagonal elements so the case in which the template is compared to itself
                        if (k == None) and (label_i == label_j) and all_similarities[i][j][1] >= threshold: #The first template != label(i) has a similarity >= t
                            k = j
                    if k != None:
                        DI[k] += 1 #End of genuine
                    FA += 1 #Impostor in parallel, distance below t but different label. No need to jump since the first label is not the impostor                 
        else:
            GR += 1 #Impostor case counted directly, FR computed through DIR

    DIR = [0 for _ in range(len(template_list))] #Detection and Identification rate
    DIR[0] = DI[0] / genuine_claims
    FRR = 1 - DIR[0] 
    FAR = FA / impostor_claims
    GRR = GR / impostor_claims
    for k in range (1, len(template_list)):
        DIR[k] = DI[k] / genuine_claims + DIR[k-1]
    return DIR, FRR, FAR, GRR

#Verification Single Template
#TODO: this has to be changed and tested
def verification_eval(template_list, threshold):
    genuine_claims, impostor_claims, all_similarities = compute_similarities(template_list)
    GA = GR = FA = FR = 0
    for template_i, i in enumerate(0, len(template_list)): #for every row (probe)
        cur_probe = template_i
        for template_j, j in enumerate(1, len(template_list)): #for every column (template)
            cur_template = template_j
            if i != j: #Do not consider main diagonal elements so the case in which the template is compared to itself
                cur_similarity = all_similarities[i][j]
                if cur_similarity >= threshold: #If the templates are similar enough
                    if cur_probe == cur_template: #the identity!! (to change)
                        GA += 1
                    else:
                        FA += 1
                else:
                    if cur_probe == cur_template:
                        FR += 1
                    else:
                        GR += 1
    GAR = GA / genuine_claims
    GRR = GR / impostor_claims
    FAR = FA / impostor_claims
    FRR = FR / genuine_claims
    return GAR, GRR, FAR, FRR