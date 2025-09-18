import sqlite3
import os
from datetime import datetime

class DatabaseModel:
    def __init__(self, db_path):
        self.db_path = db_path
        db_dir = os.path.dirname(db_path)
        os.makedirs(db_dir, exist_ok=True)

    def _execute(self, query, params=(), commit=False, fetch=None, executemany=False):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                if executemany:
                    cursor.executemany(query, params)
                else:
                    cursor.execute(query, params)
                
                if commit:
                    conn.commit()
                
                if fetch == 'one':
                    return cursor.fetchone()
                if fetch == 'all':
                    return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Erro no banco de dados: {e}")
            return None

    def create_tables(self, columns_for_creation):
        colunas_sql = ', '.join([f'"{c}" TEXT' for c in columns_for_creation])
        
        query_cadastros = f"CREATE TABLE IF NOT EXISTS cadastros (id INTEGER PRIMARY KEY AUTOINCREMENT, data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP, {colunas_sql})"
        query_rascunhos = f"CREATE TABLE IF NOT EXISTS rascunhos (id INTEGER PRIMARY KEY AUTOINCREMENT, data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP, {colunas_sql})"
        query_ajustes = "CREATE TABLE IF NOT EXISTS ajustes (id INTEGER PRIMARY KEY AUTOINCREMENT, eqpto TEXT NOT NULL UNIQUE, data_adicao TIMESTAMP DEFAULT CURRENT_TIMESTAMP, observacao TEXT, status TEXT)"
        query_historico = "CREATE TABLE IF NOT EXISTS historico_ajustes (id INTEGER PRIMARY KEY AUTOINCREMENT, eqpto TEXT, data_conclusao TIMESTAMP DEFAULT CURRENT_TIMESTAMP, status TEXT)"
        query_opcoes = "CREATE TABLE IF NOT EXISTS opcoes_combobox (id INTEGER PRIMARY KEY AUTOINCREMENT, categoria TEXT NOT NULL, valor TEXT NOT NULL, UNIQUE(categoria, valor))"

        self._execute(query_cadastros, commit=True)
        self._execute(query_rascunhos, commit=True)
        self._execute(query_ajustes, commit=True)
        self._execute(query_historico, commit=True)
        self._execute(query_opcoes, commit=True)

        self._populate_initial_options()
        
        tabelas_para_verificar = ['cadastros', 'rascunhos']
        colunas_existentes = {}
        for tabela in tabelas_para_verificar:
            rows = self._execute(f"PRAGMA table_info({tabela})", fetch='all')
            if rows:
                colunas_existentes[tabela] = {row['name'] for row in rows}

        for col in columns_for_creation:
            for tabela in tabelas_para_verificar:
                if col not in colunas_existentes.get(tabela, set()):
                    try:
                        self._execute(f"ALTER TABLE {tabela} ADD COLUMN {col} TEXT", commit=True)
                    except sqlite3.OperationalError:
                        pass
        try:
            self._execute("ALTER TABLE ajustes ADD COLUMN observacao TEXT", commit=True)
        except sqlite3.OperationalError:
            pass
        try:
            self._execute("ALTER TABLE ajustes ADD COLUMN status TEXT", commit=True)
        except sqlite3.OperationalError:
            pass

    def _populate_initial_options(self):
        initial_data = {
            'condicao': ["Acess Inv", "Acess s/Inv", "NA", "NF", "NA ABR", "NF LS", "P.O. NA", "P.O. NF", "P.O. SECC NA", "P.O. SECC NF", "SECC NA", "SECC NF", "PRIM", "SE RELI", "SE SECI", "MONOF. NF", "MONOF. NA", "MONOF. SECC NA", "MONOF. SECC NF"],
            'malha': ["Centro", "Leste", "Mantiqueira", "Norte", "Sul"],
            'motivador': ["Instalação", "Reajuste", "Relocação"],
            'midia': ["Celular", "Satélite", "Rádio", "Desconhecido", "Não enc."],
            'fabricante': ["ABB", "AMPERA", "ARTECHE", "BRUSH", "COOPER", "GeW", "HSS", "McGRAW_EDISON", "NOJA", "NU_LEC", "REYROLLE", "ROMAGNOLE", "SIEMENS", "SCHNEIDER", "TAVRIDA", "WESTINGHOUSE", "WHIPP_BOURNE", "DESCONHECIDO", "SC_ElectricCompany"],
            'telecontrolado': ["sim", "não"],
            'manobra_efetiva': ["Não", "Sim"],
            'vinculado_acessante': ["Não", "Sim"],
            'alimentador': [
                "AAA 001", "AACO202", "AACO205", "AAD 001", "AAJ 001", "AAJA001", "AAY 13", "AAY 16", "AAY 17", "ABCD01", "ABDD201", "ABRC22", "ACM 410", "ACRS208", "ACSU106", "ACSU108", "ACSU109", "ACSU110", "ACSU114", "ACSU115", "ADOD03", "ADOD05", "ADOD06", "AETD14", "AETD15", "AETD16", "AFDG001", "AFNU15", "AFNU16", "AFNU17", "AFNU18", "AFNU21", "AFNU22", "AFNU23", "AFNU24", "AFNU25", "AFPU208", "AGF 08", "AGF 10", "AGF 11", "AGJK001", "AGJK002", "AGJK003", "AGPA01", "AGST01", "AGTA01", "AGU 001", "AGV 01", "AGVE01", "AGVM01", "AHHH001", "AHJA001", "AIUF01", "AJA 001", "AJAJ001", "AJB 001", "AJC 001", "AJE 001", "AJF 001", "AJI 001", "AJJ 001", "AJK 001", "AJN 001", "AJP 001", "AJQ 001", "AJR 001", "AJT 001", "AJV 001", "AJVA001", "AJW 001", "AJX 001", "AJY 001", "AJZ 001", "AKA 001", "ALAF01", "ALDE01", "ALF 01", "ALME01", "ALNP57", "ALPI207", "ALSD204", "ALSD208", "ALSD210", "ALSS57", "ALVO88", "AMAR001", "AMAT01", "AMN 06", "AMN 07", "AMN 08", "ANA 01", "ANAD204", "ANAD205", "ANAD208", "ANAD209", "ANAD212", "ANAD213", "ANAD216", "ANAD217", "ANAF01", "ANDF01", "ANDR01", "ANFC01", "ANSF01", "AOR 03", "AOR 04", "AOR 05", "AOR 06", "AOSR202", "AOY 02", "AOY 03", "AOY 06", "APGR01", "ARAD22", "ARCO206", "ARCR205", "ARCS78", "ARGM99", "ARID201", "ARID202", "ARID203", "ARID204", "ARID205", "ARID209", "ARID210", "ARID211", "ARID212", "ARID214", "ARMA24", "ARMV99", "AROC209", "ASDF001", "ASGG001", "ASGG002", "ATAT001", "ATBH01", "ATGH01", "ATSE01", "AUIU07", "AUIU08", "AUIU12", "AUIU13", "AUIU16", "AUVU03", "AUVU04", "AUVU05", "AUVU06", "AVT 06", "AVT 07", "AVT 08", "AVT 09", "AXAU02", "AXAU03", "AXAU04", "AXAU05", "AXAU07", "AXAU10", "AXAU11", "AXAU13", "AXAU14", "AXAU17", "AXX 13", "AYN 10", "AYN 11", "AYN 13", "BAMB209", "BAR 001", "BARS01", "BBBC01", "BBBI204", "BBDM01", "BBI 02", "BBI 04", "BBI 07", "BBI 08", "BBI 09", "BBI 10", "BBIU205", "BBMB201", "BBMI202", "BBMU208", "BBUI209", "BCAD205", "BCAD206", "BCAD208", "BCAD209", "BCAD212", "BCAD213", "BCAD215", "BCAD216", "BCAU04", "BCAU05", "BCAU06", "BCAU09", "BCAU10", "BCAU11", "BCBC01", "BCNA01", "BCNM01", "BCOA01", "BCSQ416", "BCSQ417", "BCSQ418", "BCSQ419", "BCSQ420", "BCSU08", "BCSU09", "BCSU10", "BCV 05", "BCV 06", "BCV 07", "BCV 08", "BCV 12", "BCVA01", "BCVC01", "BCVF01", "BCVG01", "BCVR01", "BDDM01", "BDDN01", "BDM 05", "BDM 06", "BDM 08", "BDMA01", "BDMM01", "BDMN01", "BDMS01", "BDMT01", "BDNN01", "BDON208", "BDPD203", "BDPD204", "BDPD205", "BDPD206", "BDPD210", "BDPD211", "BDPO208", "BEDE001", "BEEE01", "BETC505", "BETC506", "BETC507", "BETC508", "BETC510", "BETC514", "BETC515", "BETC516", "BETC517", "BETC523", "BETC524", "BETC525", "BETC526", "BETD206", "BETD207", "BETD209", "BETD210", "BETD211", "BETD213", "BETD214", "BETD215", "BETD217", "BETD218", "BETD220", "BETD221", "BETD222", "BETD223", "BETD225", "BETQ404", "BETQ405", "BETQ407", "BETQ408", "BETQ410", "BETQ413", "BETQ415", "BETQ416", "BETQ417", "BETQ419", "BETT305", "BETT309", "BETT310", "BETT311", "BETT312", "BETT315", "BETT316", "BETT317", "BETT319", "BETY001", "BFM 99", "BFS 06", "BFS 07", "BGT 01", "BHA 03", "BHAA001", "BHAD10", "BHAD11", "BHAD13", "BHAD14", "BHAD17", "BHAD18", "BHAD19", "BHAD21", "BHAD24", "BHAD25", "BHAD26", "BHAD27", "BHAD30", "BHAD31", "BHAD32", "BHAD33", "BHAG01", "BHAK01", "BHAT03", "BHAT04", "BHAT05", "BHAT06", "BHAT09", "BHAT11", "BHAT12", "BHAT13", "BHAT14", "BHAT15", "BHAT16", "BHAT18", "BHAT20", "BHAW002", "BHAZ001", "BHBN03", "BHBN04", "BHBN06", "BHBN07", "BHBN10", "BHBN12", "BHBN13", "BHBN14", "BHBN16", "BHBN18", "BHBN19", "BHBN20", "BHBN24", "BHBP03", "BHBP04", "BHBP08", "BHBP09", "BHBP10", "BHBP12", "BHBP13", "BHBP14", "BHBP17", "BHBP18", "BHBP18", "BHBP19", "BHBP22", "BHBP23", "BHBP26", "BHBP27", "BHBP28", "BHBW001", "BHBX001", "BHCL04", "BHCL05", "BHCL06", "BHCL12", "BHCL13", "BHCL14", "BHCL15", "BHCL20", "BHCL21", "BHCL22", "BHCL27", "BHCL28", "BHCL29", "BHCL30", "BHCT202", "BHCT203", "BHCT206", "BHCT207", "BHCT212", "BHCT214", "BHCT218", "BHCT219", "BHCT220", "BHCT223", "BHCT224", "BHCT228", "BHCT229", "BHCT236", "BHCT237", "BHCT241", "BHCT243", "BHCT244", "BHCT247", "BHCT248", "BHCT249", "BHCT253", "BHCT254", "BHCT255", "BHCT259", "BHCT260", "BHCT261", "BHCT264", "BHCT265", "BHCT272", "BHCT273", "BHCT276", "BHCT277", "BHCT282", "BHCT284", "BHCT288", "BHCT289", "BHCT292", "BHCT293", "BHCT297", "BHCT298", "BHCZ001", "BHES01", "BHFG01", "BHGD01", "BHGF01", "BHGH01", "BHGJ01", "BHGK01", "BHGT04", "BHGT05", "BHGT07", "BHGT08", "BHGT10", "BHGT11", "BHGT13", "BHGT14", "BHGT16", "BHGT17", "BHGT19", "BHGT20", "BHGT22", "BHGT23", "BHGW001", "BHHR02", "BHHR03", "BHHR05", "BHHR06", "BHHR09", "BHHR10", "BHHR11", "BHHR12", "BHHR21", "BHHR22", "BHHR23", "BHHR24", "BHHR30", "BHJA01", "BHJE01", "BHJG01", "BHJH01", "BHJI01", "BHJJ01", "BHJK01", "BHJL01", "BHJM01", "BHJP01", "BHJT01", "BHJT02", "BHJT03", "BHJT04", "BHJT08", "BHJT10", "BHJT11", "BHJT12", "BHJT14", "BHJT15", "BHJT16", "BHJT17", "BHJT21", "BHJU01", "BHJV001", "BHJW01", "BHJX001", "BHJZ01", "BHKD01", "BHKG01", "BHKI01", "BHKK01", "BHKL01", "BHKR01", "BHLL01", "BHMA01", "BHMR05", "BHMR06", "BHMR07", "BHMR08", "BHMR09", "BHMR11", "BHMR12", "BHMR13", "BHMR21", "BHMR22", "BHMR23", "BHMR24", "BHMR26", "BHMR27", "BHNK01", "BHPJ01", "BHPM05", "BHPM07", "BHPM08", "BHPM09", "BHPM10", "BHPM14", "BHPM15", "BHPM16", "BHPM17", "BHPM18", "BHPM21", "BHPM22", "BHPM23", "BHPM24", "BHPM25", "BHPM29", "BHPM30", "BHPM31", "BHPM32", "BHPM33", "BHPU01", "BHPW001", "BHPY001", "BHPY002", "BHRN98", "BHS 05", "BHS 06", "BHS 08", "BHS 13", "BHS 16", "BHSE05", "BHSE06", "BHSE07", "BHSE08", "BHSE10", "BHSE11", "BHSE12", "BHSE13", "BHSE14", "BHSE15", "BHSE16", "BHSE17", "BHSE19", "BHSE20", "BHSE21", "BHSE22", "BHSG01", "BHSK01", "BHSL01", "BHSM01", "BHSN03", "BHSN04", "BHSN05", "BHSN07", "BHSN13", "BHSN15", "BHSN16", "BHSN18", "BHSN24", "BHSN25", "BHSN27", "BHSN28", "BHSN35", "BHSN36", "BHSN38", "BHSN39", "BHSO04", "BHSO05", "BHSO07", "BHSO08", "BHSO10", "BHSO11", "BHSO13", "BHSO14", "BHSO19", "BHSO23", "BHSO24", "BHSO25", "BHSO28", "BHSO29", "BHSP01", "BHSR04", "BHSR05", "BHSR07", "BHSR08", "BHSR12", "BHSR13", "BHSR14", "BHSR15", "BHSR19", "BHSR20", "BHSR21", "BHSR22", "BHSR26", "BHSR27", "BHSR29", "BHSR30", "BHSV02", "BHSV03", "BHSV13", "BHSV14", "BHSV15", "BHSV16", "BHSV36", "BHSV37", "BHTE01", "BHTG01", "BHTT001", "BHUR01", "BHVK01", "BHVN01", "BHVV001", "BHWA001", "BHWB001", "BHWC001", "BHWD001", "BHWH001", "BHWI001", "BHWJ001", "BHWK001", "BHWL001", "BHWM001", "BHWN001", "BHWO001", "BHWP001", "BHWU001", "BHWW001", "BHWY001", "BHWZ001", "BHXA001", "BHXS01", "BHYA001", "BHYB001", "BHYC001", "BHYD001", "BHYE001", "BHYF001", "BHYG001", "BHYH001", "BHYI001", "BHYJ001", "BHYK001", "BHYL001", "BHYM001", "BHYN001", "BHYO001", "BHYP001", "BHYQ001", "BHYR001", "BHYS001", "BHYT001", "BHYU001", "BHYV001", "BHYW001", "BHYY001", "BHYZ03", "BHZA001", "BHZB001", "BHZC001", "BHZG01", "BHZH001", "BHZI001", "BHZJ001", "BHZL001", "BHZN001", "BHZO001", "BHZP001", "BHZQ001", "BHZR001", "BHZS001", "BHZT001", "BHZU001", "BHZV001", "BHZW001", "BHZY001", "BHZZ001", "BIBT01", "BIID203", "BIID205", "BIID207", "BIIU04", "BIIU05", "BIIU09", "BIMT01", "BIR 01", "BIRI01", "BJDP01", "BMBI203", "BMBU206", "BMN 04", "BMN 05", "BMN 07", "BMNG01", "BMNN01", "BMNO01", "BMNT01", "BMO 05", "BMO 06", "BMO 07", "BMO 09", "BMS 12", "BMS 14", "BMS 15", "BMSE99", "BMSS01", "BMUI201", "BNMI01", "BNMU80", "BNPP01", "BNR 04", "BNR 05", "BNR 06", "BNR 07", "BNSS01", "BNTT01", "BOCV01", "BOED207", "BOED208", "BOED209", "BOED210", "BOED211", "BOEF01", "BOMI01", "BOMR01", "BOMS01", "BOSE01", "BPDO208", "BPOD201", "BPSU09", "BPSU10", "BRAF01", "BRBH01", "BRDD205", "BRDD206", "BRDD208", "BRDD209", "BRDD213", "BRDD214", "BRDM01", "BRL 05", "BRL 06", "BRL 07", "BRM 111", "BRMT01", "BRR 01", "BRSM01", "BRU 002", "BRZF01", "BSF 01", "BSJT01", "BSOT312", "BSOT313", "BSOT315", "BTBR01", "BTCO01", "BTDM01", "BTGE01", "BTJF001", "BTME01", "BTNO01", "BTPA01", "BTPD01", "BTTE01", "BTTO01", "BTTP999", "BTTR01", "BTTT001", "BTZD203", "BTZD204", "BTZD205", "BTZD206", "BUEN01", "CABO01", "CADU208", "CAM 01", "CAMC01", "CAME01", "CAMF01", "CAMG01", "CAMP78", "CAMQ01", "CAMT01", "CAMU01", "CAMY01", "CAN 01", "CAND01", "CANO01", "CAPR209", "CAQF01", "CAQU05", "CAQU06", "CAQU07", "CAR 001", "CARM68", "CATG01", "CATL201", "CAX 01", "CAX 02", "CAX 07", "CAX 08", "CAX 09", "CAX 10", "CBB 01", "CBFI01", "CBLF01", "CBM 01", "CBTT24", "CCAP204", "CCC 410", "CCCP01", "CCDJ01", "CCH 01", "CCHD207", "CCHD208", "CCHU13", "CCHU14", "CCHU15", "CCJU204", "CCLA225", "CCLL205", "CCMC201", "CCMI205", "CCP 07", "CCP 08", "CCPA206", "CCPD203", "CCPD204", "CCPD205", "CCPD206", "CCPO204", "CCPR201", "CCRO204", "CCTM78", "CCU 410", "CCUR14", "CCVL01", "CCY 01", "CCY 02", "CCYD203", "CCYD204", "CCYD205", "CCYD206", "CCYT302", "CCYT303", "CCYT304", "CCYT305", "CDC 11", "CDCJ78", "CDSF01", "CDSF02", "CEL 06", "CEL 07", "CEL 08", "CEL 09", "CEMC502", "CEMC503", "CEMM001", "CEMQ402", "CEMQ403", "CEMQ404", "CEMQ406", "CEMQ407", "CEMQ408", "CEMQ415", "CEMQ416", "CEMQ417", "CEMQ419", "CEMQ420", "CEMQ421", "CEMT01", "CEMT02", "CEMT03", "CEMT04", "CEMT07", "CEMT10", "CEMT12", "CEMT13", "CEMT14", "CEMT20", "CEMT21", "CEMT22", "CEMT24", "CEMT25", "CEMW001", "CEO 07", "CEO 08", "CETU04", "CETU08", "CETU09", "CETU10", "CETU11", "CEVO01", "CFBT01", "CFD 77", "CFGB01", "CGAU02", "CGAU03", "CGAU04", "CGAU05", "CGAU06", "CGAU10", "CGAU11", "CGAU12", "CGAU13", "CGAU14", "CGS 01", "CHGM01", "CHHD01", "CHPD01", "CICM01", "CICM02", "CICM03", "CICM04", "CICM05", "CICM15", "CICM26", "CICM27", "CICM28", "CICM30", "CICM31", "CICM32", "CICM34", "CICM35", "CINC01", "CINC02", "CINC03", "CINC05", "CINC07", "CINC09", "CINC10", "CINC11", "CINC18", "CINC19", "CINC20", "CINC22", "CINZ001", "CINZ002", "CIOD214", "CISL05", "CISL06", "CISL07", "CISL12", "CISL13", "CISS001", "CITU02", "CITU04", "CITU05", "CITU06", "CITU10", "CJDD01", "CLAR57", "CLCL01", "CLDU204", "CLHU03", "CLHU04", "CLHU05", "CLHU06", "CLHU07", "CLHU09", "CLKM25", "CLLB01", "CLLO01", "CLRV204", "CLS 06", "CLS 07", "CLS 08", "CLUD207", "CLUD208", "CLUD209", "CLUU07", "CLUU08", "CLUU09", "CLVV01", "CMCM208", "CMD 06", "CMD 08", "CMD 09", "CMDD203", "CMDD204", "CMDD205", "CMDD206", "CMF 01", "CMG 05", "CMG 06", "CMG 07", "CMH 03", "CMH 05", "CMH 06", "CMH 80", "CMID212", "CMID214", "CMID216", "CMID217", "CMMN01", "CMN 02", "CMN 03", "CMN 04", "CMN 05", "CMOP204", "CMOR208", "CMPB01", "CMPS78", "CMT 03", "CMT 04", "CMT 05", "CMT 06", "CMTA99", "CMZL01", "CMZZ01", "CNH 05", "CNH 06", "CNH 07", "CNIR01", "CNLU07", "CNLU08", "CNLU09", "CNLU10", "CNLU18", "CNLU19", "CNLU20", "CNLU21", "CNN 05", "CNN 06", "CNN 08", "CNN 09", "CNS 04", "CNS 05", "CNS 06", "CNTD20", "CNTT10", "CNTU10", "CNTZ10", "COAG01", "COAP205", "CODI57", "COFI01", "COJ 07", "COJ 08", "COJ 09", "COJW01", "COM 04", "COM 05", "COM 06", "COMD203", "COMD204", "COMD205", "COMD206", "CONC204", "CONF01", "CONU03", "CONU04", "CONU05", "CONU07", "CONU08", "CONU09", "CONU10", "CORR01", "CORT01", "COSA01", "COSF01", "COVV01", "CPCH01", "CPG 07", "CPG 08", "CPG 09", "CPGM99", "CPO 05", "CPO 06", "CPO 07", "CPO 08", "CPO 13", "CPO 14", "CPO 15", "CPOF01", "CPX 01", "CQE 02", "CQE 05", "CQLU103", "CQLU104", "CQLU105", "CQLU106", "CRC 02", "CRC 03", "CRC 04", "CRCC57", "CRCD203", "CRCD204", "CRCD205", "CRCD206", "CRCT30", "CRCU10", "CRDT312", "CRDT313", "CRDT316", "CRDT317", "CRF 10", "CRF 12", "CRF 14", "CRF 15", "CRF 18", "CRF 21", "CRF 22", "CRIC301", "CRJJ01", "CRJS01", "CRL 03", "CRL 04", "CRL 05", "CRL 06", "CRL 07", "CRL 12", "CRL 13", "CRL 14", "CRL 16", "CRL 17", "CRM 04", "CRM 05", "CRM 07", "CRM 12", "CRM 15", "CRMO205", "CRNT01", "CROM208", "CRRV01", "CRSF01", "CRTP01", "CRTU01", "CRUV01", "CRUZ01", "CRVE01", "CRVO01", "CSAM99", "CSAU06", "CSAU07", "CSAU08", "CSN 05", "CSN 06", "CSN 08", "CSN 09", "CSN 10", "CSTU03", "CSTU04", "CSTU05", "CSTU06", "CTGM01", "CTM 01", "CTR 12", "CTR 13", "CTR 14", "CTR 15", "CUG 03", "CUG 05", "CUG 07", "CUG 08", "CURN01", "CUUR01", "CUVD02", "CUVD03", "CUVD04", "CUVD05", "CUVD06", "CUVD14", "CUVF01", "CUVQ02", "CUVQ403", "CUVQ404", "CUVQ405", "CUVQ406", "CUVS01", "CUVT303", "CUVT304", "CUVT305", "CUVT306", "CVED205", "CVED206", "CVED209", "CVED210", "CVLL01", "CVLV01", "CVVV01", "CXBU01", "DDD 410", "DDDI52", "DDI 09", "DDID203", "DDID204", "DDID205", "DDID206", "DDNT01", "DEEE57", "DEGT01", "DEPE01", "DER 410", "DFNP201", "DIAM01", "DINP208", "DITA01", "DIVP67", "DJAJ001", "DJKA001", "DLNP208", "DLS 410", "DLV 99", "DMAI01", "DMAT01", "DMIA01", "DMIT01", "DMMT01", "DMTI01", "DMTT01", "DMTU06", "DMTU07", "DMTU08", "DMTU09", "DMTU12", "DMTY01", "DMUD01", "DMUF01", "DMUH01", "DMUI01", "DMUN01", "DMUQ01", "DMUR01", "DMUY01", "DNMM01", "DNPL201", "DNPV205", "DOIS204", "DPLN208", "DPNV204", "DRAF01", "DSCW01", "DSJD01", "DSV 04", "DSV 06", "DSV 07", "DTAS01", "DTNN01", "DTTA01", "DUD 410", "DVIN202", "DVIP204", "DVLD202", "DVLD203", "DVLD204", "DVLD206", "DVLD207", "DVLD210", "DVLD211", "DVLD212", "DVLD213", "DVLD215", "DVLI205", "DVLP55", "DVLU03", "DVLU04", "DVLU05", "DVLU06", "DVLU10", "DVLU12", "DVLU13", "DVLU14", "DVNL201", "DVNP205", "DVOL203", "DVOU03", "DVOU04", "DVOU05", "DVOU06", "DVPI208", "DVPL205", "DVSE99", "DVVN205", "EDK 09", "EEE 410", "EEV 410", "EFIG01", "ELMU103", "ELMU104", "ELMU105", "ELMU106", "EMGT10", "ENC 07", "ENC 11", "ENC 12", "ENC 13", "ENG 06", "ENG 07", "ENGN01", "EPNN01", "EPS 08", "EPSU03", "EPSU04", "EPSU05", "EPSU06", "ERGR01", "ERMG12", "ERMI13", "ERR 410", "ESGB01", "ESID208", "ESIN99", "ESM 01", "ESQ 01", "ESR 07", "ESR 08", "ESR 09", "ESR 15", "ESR 17", "ESR 18", "ESTI99", "EVE 410", "EVV 410", "EWB 02", "EWBT01", "EWU 01", "FAGK001", "FALF01", "FAND01", "FBDM01", "FBHS01", "FBPS01", "FCAL01", "FCAM01", "FCBO01", "FCCA01", "FCCS01", "FCDD01", "FCDS01", "FCLD01", "FCOP01", "FCPO01", "FCS 16", "FCS 17", "FCS 18", "FCS 19", "FCSA01", "FCSD203", "FCSD204", "FCSD205", "FCSD206", "FCST01", "FDM 01", "FEIX01", "FFF 01", "FFLC01", "FFLX01", "FFMD01", "FGIT01", "FGJG001", "FICT07", "FIDD01", "FILL01", "FIO 12", "FIO 13", "FIPY001", "FITD01", "FIXX01", "FJAH001", "FJCT01", "FLAB01", "FLAV01", "FLCS01", "FLDX01", "FLLA01", "FLLX01", "FLNN01", "FLNS01", "FLSC01", "FLSS01", "FLVA01", "FLXA01", "FLXF01", "FLXX01", "FMAD202", "FMAD203", "FMAD204", "FMAD206", "FMAD207", "FMAD208", "FMAD215", "FMAD216", "FMAD217", "FMAD219", "FMAD220", "FMAD221", "FMGA204", "FMGG208", "FMIG201", "FMM 410", "FMMG205", "FMUZ01", "FMZB01", "FOMA208", "FOMG01", "FORF01", "FORG78", "FORM78", "FORT57", "FOUF01", "FPAL01", "FPQO01", "FPSU01", "FRBE001", "FRDU81", "FRDU82", "FRDU83", "FRDU84", "FRE 555", "FRGA202", "FRMA78", "FRMG78", "FRRC01", "FRSC04", "FRUD206", "FRUD207", "FRUD209", "FRUD212", "FRUD213", "FRUU08", "FRUU12", "FRUU13", "FRUU14", "FRUU16", "FRVA01", "FSAA01", "FSAO01", "FSBC01", "FSCS01", "FSDG654", "FSDM01", "FSER01", "FSFP01", "FSNT01", "FSPU01", "FSRC01", "FTCS01", "FTLA203", "FTLM208", "FTMN201", "FTRE204", "FUN 001", "FVAR01", "FVIR01", "FXA 05", "FXA 06", "FXAA01", "FXAD201", "FXAD202", "FXAD203", "FXAD204", "FXAG01", "FXAS01", "FXND01", "FXR 01", "FZAE01", "GABR01", "GADD01", "GAER11", "GAJF01", "GALA01", "GALD01", "GALO01", "GAR 01", "GARB01", "GARE01", "GARG01", "GARP01", "GBAD01", "GBAT999", "GBBD01", "GBBK01", "GBBM01", "GBBT999", "GBCA01", "GBCP01", "GBFA01", "GBFR01", "GBGT999", "GBHN001", "GBHS999", "GBIT999", "GBJF01", "GBJK01", "GBKT999", "GBLJ01", "GBLV01", "GBMN999", "GBMT999", "GBNM01", "GBOA17", "GBOS01", "GBPE01", "GBPI01", "GBPO01", "GBPT999", "GBRT999", "GBS 99", "GBSC01", "GBSD01", "GBSV01", "GBT 01", "GBTB01", "GBTE999", "GBTG001", "GBTH999", "GBTI01", "GBTL999", "GBTM01", "GBTQ999", "GBTR999", "GBTS999", "GBTT01", "GBTY01", "GBTZ01", "GBVT999", "GBWC01", "GBWT01", "GBYT999", "GCAA08", "GCAL116", "GCAR16", "GCAU45", "GCBE01", "GCBR51", "GCBU28", "GCC 10", "GCCA17", "GCCD13", "GCCM53", "GCCO22", "GCDU41", "GCFR55", "GCHI01", "GCI 10", "GCIA48", "GCIB10", "GCIM24", "GCIR11", "GCIU58", "GCL 50", "GCLA06", "GCLF10", "GCLN29", "GCLU42", "GCM 10", "GCMC10", "GCME17", "GCML28", "GCMM54", "GCMN59", "GCMO62", "GCMP01", "GCMR30", "GCMT69", "GCN 13", "GCNU40", "GCP 06", "GCPA10", "GCPE17", "GCPI31", "GCPN42", "GCPO10", "GCPR14", "GCPT23", "GCRA20", "GCRE52", "GCRP115", "GCRU50", "GCSA50", "GCSJ60", "GCSM54", "GCSS61", "GCU 10", "GCUA57", "GCUB15", "GCUD22", "GCUE08", "GCUL20", "GCUN10", "GCUR06", "GCUU14", "GCV 111", "GCVB01", "GCXA56", "GDBT99", "GDCD01", "GDDS01", "GDEX01", "GDFJ01", "GDIL01", "GDIM01", "GDM 07", "GDM 08", "GDM 09", "GDMO02", "GDRP01", "GDSA01", "GDSS01", "GDVL01", "GEA 01", "GEAS01", "GEAT01", "GEBA01", "GEBI001", "GEBR001", "GEBS999", "GEBT999", "GEDA001", "GEDS01", "GEEE01", "GEEQ01", "GEGA001", "GEGI001", "GEHC001", "GEHE001", "GEL 11", "GEL 12", "GELD001", "GELE001", "GEMN01", "GEMT01", "GENV01", "GEOD01", "GEPI001", "GEPR01", "GEPU001", "GERB01", "GERC01", "GERD01", "GERE01", "GERF001", "GERM001", "GERR01", "GERV57", "GERW001", "GERZ001", "GESF01", "GETY001", "GEVS01", "GEWD01", "GEWF01", "GEWW01", "GFBA01", "GFDG01", "GFDS01", "GFEK01", "GFFF01", "GFFT01", "GFGF01", "GFJU01", "GFRE01", "GFRO01", "GFRT01", "GFRX01", "GFSW01", "GFTR01", "GFTT01", "GFYU01", "GGAD01", "GGAG01", "GGAN01", "GGAS01", "GGAW01", "GGBP01", "GGBR01", "GGBT999", "GGCD01", "GGCF01", "GGCR01", "GGDC01", "GGDE01", "GGDF01", "GGDL01", "GGDM01", "GGDO01", "GGDW01", "GGEI01", "GGEL01", "GGEN01", "GGEQ01", "GGFA01", "GGFC01", "GGFT01", "GGG 410", "GGGG01", "GGGN01", "GGGT01", "GGHD01", "GGIB01", "GGIE01", "GGIL01", "GGIZ01", "GGJF01", "GGJO01", "GGJQ01", "GGLD01", "GGLH01", "GGLP01", "GGLU103", "GGLU104", "GGLU105", "GGLU106", "GGMA01", "GGMD01", "GGME01", "GGMM01", "GGMP01", "GGNO01", "GGNT01", "GGOA01", "GGOJ01", "GGON01", "GGOS01", "GGPB01", "GGPC01", "GGPI01", "GGPM01", "GGQU01", "GGRB01", "GGRC01", "GGRO01", "GGRR01", "GGRT01", "GGSA01", "GGSC01", "GGSG01", "GGSJ01", "GGSO01", "GGST01", "GGTA01", "GGTE01", "GGTO01", "GGTP01", "GGTR01", "GGTX01", "GGTZ01", "GGUI01", "GGVI01", "GGXT01", "GHDE01", "GHE 10", "GHE 12", "GHE 14", "GHE 15", "GHE 16", "GHFR01", "GHHH01", "GHHK01", "GHHS01", "GHJK999", "GHLP01", "GHSG001", "GHSH001", "GHTM999", "GHTR01", "GHYT01", "GHYY01", "GIFY01", "GIGB01", "GIOL01", "GITA99", "GJFA01", "GJFB01", "GJFC01", "GJFD01", "GJFE01", "GJHG01", "GJJO01", "GJKI01", "GJKL999", "GJKU01", "GJKY01", "GJKZ01", "GJMM01", "GJNX01", "GJTM999", "GJUI01", "GJUO01", "GKAD01", "GKBT999", "GKIG01", "GKJD01", "GKUY01", "GLAD01", "GLDU001", "GLGR01", "GLJK01", "GLJP01", "GLJS01", "GLLP01", "GLPC01", "GLRS01", "GMBJ01", "GMBT01", "GMCA99", "GMCF99", "GMCM99", "GMCO99", "GMCP99", "GMDV99", "GMDY01", "GMG 502", "GMGA85", "GMGD506", "GMGE01", "GMGL01", "GMGM85", "GMGP85", "GMGQ01", "GMGU01", "GMHJ01", "GMHT01", "GMIL01", "GMIT99", "GMJF01", "GMJI01", "GMJL01", "GMJT999", "GMKK01", "GMKT01", "GML 07", "GMMC01", "GMPI99", "GMPM99", "GMRE01", "GMRQ99", "GMSR99", "GMT 01", "GMTA01", "GMTD999", "GMTE999", "GMTI001", "GMTJ999", "GMTO999", "GMTT01", "GMTU01", "GMTX01", "GMTY999", "GMVL01", "GMXT01", "GMY 506", "GMZZ01", "GNAX01", "GNBH01", "GNBM01", "GNBO01", "GNBR01", "GNBW01", "GNDS01", "GNES01", "GNFA01", "GNFN01", "GNGK01", "GNGR01", "GNHT01", "GNIN01", "GNJH01", "GNJI01", "GNJM01", "GNJZ01", "GNKA01", "GNKF01", "GNKS01", "GNLB01", "GNLJ01", "GNLV01", "GNMC01", "GNMN01", "GNMR01", "GNMU01", "GNMV01", "GNNB01", "GNNH01", "GNNT01", "GNNZ01", "GNOT01", "GNPB01", "GNPG01", "GNQN01", "GNRF01", "GNSD01", "GNSE01", "GNSJ01", "GNSZ01", "GNTD01", "GNUF01", "GNUQ01", "GNVA01", "GNVD01", "GNVI01", "GNWL01", "GOBT999", "GOLA01", "GOLI01", "GOLU01", "GOPI01", "GOPS01", "GOVD01", "GOVD02", "GOVD80", "GPDS01", "GPE 13", "GPED04", "GPED05", "GPED06", "GPED08", "GPED09", "GPED12", "GPED13", "GPED15", "GPED16", "GPED17", "GPEF01", "GPFF01", "GPJK01", "GPPI01", "GPPO01", "GPSV01", "GQBD01", "GQBT999", "GQQX01", "GRAM001", "GRAX01", "GRBH01", "GRBI01", "GRBT999", "GRC 01", "GRDP01", "GRFS01", "GRFU01", "GRGH01", "GRIB208", "GRM 001", "GRMA01", "GRMB01", "GRMC01", "GRMD01", "GRME01", "GRMF01", "GRMH01", "GRMI01", "GRMJ01", "GRMK01", "GRML01", "GRMN01", "GRMO01", "GRMP01", "GRMQ01", "GRMR01", "GRMS01", "GRMT01", "GRMU01", "GRMV01", "GRMX01", "GRMY01", "GRMZ01", "GRPO001", "GRRR01", "GRSA01", "GRSO01", "GRST01", "GRTA01", "GRTI01", "GRTJ01", "GRTL01", "GRTM01", "GRTN01", "GRTO01", "GRTP01", "GRTQ01", "GRTR01", "GRTT01", "GRTU01", "GRTW01", "GRVG01", "GRYT01", "GSAW01", "GSBH999", "GSBK01", "GSBT999", "GSDF01", "GSFG01", "GSGE01", "GSJA01", "GSJB01", "GSJC01", "GSJD01", "GSJE01", "GSJF01", "GSJH01", "GSJI01", "GSJJ01", "GSJK01", "GSJL01", "GSJU01", "GSKJ01", "GSND01", "GSRM99", "GSRQ99", "GSS 01", "GSSE01", "GSSS01", "GSTQ01", "GSVC999", "GTAS01", "GTBT01", "GTCP01", "GTDF01", "GTDL01", "GTFD01", "GTGA208", "GTGT01", "GTIU01", "GTJF01", "GTJO01", "GTJS001", "GTLO01", "GTM 01", "GTMA999", "GTML01", "GTMO101", "GTMU01", "GTMV01", "GTOV01", "GTPN01", "GTPO01", "GTQX01", "GTRE01", "GTRG410", "GTRM01", "GTRP01", "GTRV01", "GTSA22", "GTTA01", "GTTC01", "GTTE01", "GTTF01", "GTTQ01", "GTTR01", "GTTT01", "GTU 410", "GTVA01", "GUA 01", "GUBT999", "GUED203", "GUED204", "GUED205", "GUED206", "GUIL01", "GUIO01", "GUMT99", "GURI57", "GUST01", "GUTM01", "GUTY001", "GUUO01", "GUYI01", "GUYT01", "GVG 13", "GVLF01", "GVSC502", "GVSC503", "GVSC504", "GVSC506", "GVSC507", "GVSC508", "GVSC515", "GVSC516", "GVSC517", "GVSC519", "GVSC5"
            ]
        }
        
        data_to_insert = []
        
        existing_categories_rows = self._execute("SELECT DISTINCT categoria FROM opcoes_combobox", fetch='all')
        existing_categories = {row['categoria'] for row in existing_categories_rows} if existing_categories_rows else set()

        for category, values in initial_data.items():
            if category not in existing_categories:
                for value in values:
                    data_to_insert.append((category, value))
        
        if data_to_insert:
            self._execute("INSERT OR IGNORE INTO opcoes_combobox (categoria, valor) VALUES (?, ?)", data_to_insert, commit=True, executemany=True)

    def save_record(self, data_dict, table_name):
        data_to_save = data_dict.copy()
        data_to_save.pop('id', None)
        data_to_save.pop('data_registro', None)
        keys = ', '.join([f'"{k}"' for k in data_to_save.keys()])
        placeholders = ', '.join(['?'] * len(data_to_save))
        values = list(data_to_save.values())
        query = f"INSERT INTO {table_name} ({keys}) VALUES ({placeholders})"
        self._execute(query, values, commit=True)

    def save_draft(self, data_dict):
        eqpto = data_dict.get('eqpto')
        if not eqpto: return
        self._execute("DELETE FROM rascunhos WHERE eqpto = ?", (eqpto,), commit=True)
        self.save_record(data_dict, 'rascunhos')

    def save_final_and_manage_lists(self, data_dict):
        eqpto = data_dict.get('eqpto')
        if not eqpto: return
        self._execute("DELETE FROM cadastros WHERE eqpto = ?", (eqpto,), commit=True)
        self.save_record(data_dict, 'cadastros')
        self._execute("INSERT OR IGNORE INTO ajustes (eqpto) VALUES (?)", (eqpto,), commit=True)
        self._execute("DELETE FROM rascunhos WHERE eqpto = ?", (eqpto,), commit=True)

    def get_recent_equipments(self, limit=50):
        query = "SELECT eqpto, ns, data, alimentador FROM cadastros WHERE eqpto != '' ORDER BY data_registro DESC LIMIT ?"
        return self._execute(query, (limit,), fetch='all')

    def get_all_draft_equipments(self):
        query = "SELECT eqpto, ns, data, alimentador FROM rascunhos WHERE eqpto != '' ORDER BY data_registro DESC"
        return self._execute(query, fetch='all')

    def delete_drafts(self, eqpto_list):
        params = [(eq,) for eq in eqpto_list]
        self._execute("DELETE FROM rascunhos WHERE eqpto = ?", params, commit=True, executemany=True)

    def get_record_by_id(self, record_id, table_name):
        query = f"SELECT * FROM {table_name} WHERE id = ?"
        return self._execute(query, (record_id,), fetch='one')

    def get_latest_id_for_equipment(self, eqpto, table_name):
        query = f"SELECT id FROM {table_name} WHERE eqpto = ? ORDER BY data_registro DESC LIMIT 1"
        return self._execute(query, (eqpto,), fetch='one')

    def get_pending_adjustments(self):
        query = """
        SELECT a.eqpto, a.status, c.autor, c.data, c.malha, c.alimentador, c.fabricante, c.comando
        FROM ajustes a
        JOIN (
            SELECT *, ROW_NUMBER() OVER(PARTITION BY eqpto ORDER BY data_registro DESC) as rn 
            FROM cadastros
        ) c ON a.eqpto = c.eqpto 
        WHERE c.rn = 1 
        ORDER BY a.data_adicao DESC
        """
        return self._execute(query, fetch='all')

    def complete_adjustment(self, eqpto, status):
        self._execute("INSERT INTO historico_ajustes (eqpto, status) VALUES (?, ?)", (eqpto, status), commit=True)
        self._execute("DELETE FROM ajustes WHERE eqpto = ?", (eqpto,), commit=True)

    def get_observation(self, eqpto):
        return self._execute("SELECT observacao FROM ajustes WHERE eqpto = ?", (eqpto,), fetch='one')

    def update_observation(self, eqpto, text):
        self._execute("UPDATE ajustes SET observacao = ? WHERE eqpto = ?", (text, eqpto), commit=True)
        
    def update_adjustment_status(self, eqpto_list, status):
        params = [(status, eq,) for eq in eqpto_list]
        self._execute("UPDATE ajustes SET status = ? WHERE eqpto = ?", params, commit=True, executemany=True)

    def get_adjustments_history(self, limit=100):
        query = "SELECT eqpto, data_conclusao, status FROM historico_ajustes ORDER BY data_conclusao DESC LIMIT ?"
        return self._execute(query, (limit,), fetch='all')

    def search_records(self, filters):
        query = """
        SELECT id, eqpto, malha, alimentador, data_registro
        FROM (
            SELECT *, ROW_NUMBER() OVER(PARTITION BY eqpto ORDER BY data_registro DESC) as rn
            FROM cadastros
        )
        WHERE rn = 1
        """
        condicoes = []
        params = []
        for campo, valor in filters.items():
            if valor:
                condicoes.append(f"{campo} LIKE ?")
                params.append(f"%{valor}%")
        if condicoes:
            query += " AND " + " AND ".join(condicoes)
        query += " ORDER BY data_registro DESC"
        return self._execute(query, tuple(params), fetch='all')

    # --- Funções para o Módulo de Gestão ---
    def get_categorias(self):
        query = "SELECT DISTINCT categoria FROM opcoes_combobox ORDER BY categoria"
        rows = self._execute(query, fetch='all')
        return [row['categoria'] for row in rows] if rows else []

    def get_opcoes_por_categoria(self, categoria):
        query = "SELECT id, valor FROM opcoes_combobox WHERE categoria = ? ORDER BY valor"
        return self._execute(query, (categoria,), fetch='all')

    def adicionar_opcao(self, categoria, valor):
        query = "INSERT OR IGNORE INTO opcoes_combobox (categoria, valor) VALUES (?, ?)"
        self._execute(query, (categoria, valor), commit=True)

    def editar_opcao(self, id_opcao, novo_valor):
        query = "UPDATE opcoes_combobox SET valor = ? WHERE id = ?"
        self._execute(query, (novo_valor, id_opcao), commit=True)

    def deletar_opcao(self, id_opcao):
        query = "DELETE FROM opcoes_combobox WHERE id = ?"
        self._execute(query, (id_opcao,), commit=True)

    def deletar_opcoes_por_categoria(self, categoria):
        query = "DELETE FROM opcoes_combobox WHERE categoria = ?"
        self._execute(query, (categoria,), commit=True)
