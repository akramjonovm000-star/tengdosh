from bs4 import BeautifulSoup

html_content = """
    <div class="box box-success ">
        <div class="box-body no-padding">
            <table class="table table-striped">
                <thead>
                                <tr>
                    <th width="50px"></th>
                    <th width="50%">Fanlar</th>
                    <th>JN</th>
                    <th>ON</th>
                    <th>YN</th>
                    <th>Umumiy</th>
                </tr>
                </thead>
                <tbody>

                                                    <tr>
                        <td>1</td>
                        <td>O'ZBEKISTONNING ENG YANGI TARIXI</td>
                                                <td>
                                                            5.0                                                                                        <a class="showModalButton" ><i class="fa fa-eye-slash"></i></a>                        </td>
                        <td>5.0</td>
                        <td></td>
                        <td></td>
                                            </tr>
                                    <tr>
                        <td>7</td>
                        <td>PR VA REKLAMA TARIXI</td>
                                                    <td>
                                                                                                    4.0                                
                                <a class="showModalButton" ><i class="fa fa-eye-slash"></i></a>                            </td>
                            <td>4.0</td>
                            <td>5.0</td>
                            <td>5.0</td>
                                            </tr>
                </tbody>
            </table>
        </div>
    </div>
"""

def parse():
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table')
    headers = [th.get_text(strip=True) for th in table.find_all('th')]
    print(f"Headers: {headers}")
    
    idx_subj = -1
    idx_jn = -1
    
    for i, h in enumerate(headers):
        if "Fanlar" in h: idx_subj = i
        if "JN" in h: idx_jn = i
    
    print(f"Indices: Subj={idx_subj}, JN={idx_jn}")
    
    rows = table.find('tbody').find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        if len(cols) < max(idx_subj, idx_jn): continue
        
        subj_name = cols[idx_subj].get_text(strip=True)
        jn_raw = cols[idx_jn].get_text(strip=True)
        
        # Clean
        try:
             # Split by space to ignore trailing icon text/garbage
             jn_val = float(jn_raw.split()[0])
        except:
             jn_val = 0.0
             
        print(f"Subject: {subj_name} | JN Raw: '{jn_raw}' | JN Float: {jn_val}")

if __name__ == "__main__":
    parse()
