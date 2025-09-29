#!/usr/bin/env python3
"""
Создание тестовой IFC модели для проверки конвертации 3D → 2D
"""

import os
import struct
import datetime

def create_simple_ifc_file(filename="test_model.ifc"):
    """
    Создает простую тестовую IFC модель с фиксированными параметрами:
    - Квартира 50 м²
    - 2 комнаты, 1 санузел
    - Окна и двери
    - Базовые стены
    """
    
    # Базовый IFC заголовок
    ifc_content = '''ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
FILE_NAME('{filename}','{timestamp}',('Test User'),('Test Organization'),'Test Software','Test Software','');
FILE_SCHEMA(('IFC4'));
ENDSEC;

DATA;
#1=IFCPROJECT('{project_id}',#2,'Test Project','Test Description',$,#3,#4,$);
#2=IFCOWNERHISTORY(#5,#6,$,.ADDED.,$,#5);
#3=IFCRELCONTAINEDINSPATIALSTRUCTURE('{rel_id}','Spatial Structure',$,#7,#1);
#4=IFCRELAGGREGATES('{agg_id}','Aggregation',$,#1,#8);
#5=IFCPERSONANDORGANIZATION(#9,#10,$);
#6=IFCAPPLICATION(#11,'Test Software','Test Software','1.0');
#7=IFCBUILDING('{building_id}','Test Building','Test Building Description',$,#12,$,$,$,.ELEMENT.,$,#13);
#8=IFCSITE('{site_id}','Test Site','Test Site Description',$,#14,$,$,$,$,.ELEMENT.,$);
#9=IFCPERSON('Test User','Test','Test','Test','Test','Test','Test','Test');
#10=IFCORGANIZATION('Test Organization','Test','Test','Test','Test');
#11=IFCAPPLICATION(#9,'Test Software','Test Software','1.0');
#12=IFCLOCALPLACEMENT(#15,#16);
#13=IFCLOCALPLACEMENT(#17,#18);
#14=IFCLOCALPLACEMENT(#19,#20);
#15=IFCAXIS2PLACEMENT3D(#21,#22,#23);
#16=IFCDIRECTION('Z',(0.,0.,1.));
#17=IFCAXIS2PLACEMENT3D(#24,#25,#26);
#18=IFCDIRECTION('Z',(0.,0.,1.));
#19=IFCAXIS2PLACEMENT3D(#27,#28,#29);
#20=IFCDIRECTION('Z',(0.,0.,1.));
#21=IFCCARTESIANPOINT('Origin',(0.,0.,0.));
#22=IFCDIRECTION('X',(1.,0.,0.));
#23=IFCDIRECTION('Y',(0.,1.,0.));
#24=IFCCARTESIANPOINT('Building Origin',(0.,0.,0.));
#25=IFCDIRECTION('Building X',(1.,0.,0.));
#26=IFCDIRECTION('Building Y',(0.,1.,0.));
#27=IFCCARTESIANPOINT('Site Origin',(0.,0.,0.));
#28=IFCDIRECTION('Site X',(1.,0.,0.));
#29=IFCDIRECTION('Site Y',(0.,1.,0.));

#30=IFCBUILDINGSTOREY('{storey_id}','Ground Floor','Ground Floor Description',$,#31,$,$,.ELEMENT.,$);
#31=IFCLOCALPLACEMENT(#32,#33);
#32=IFCAXIS2PLACEMENT3D(#34,#35,#36);
#33=IFCDIRECTION('Z',(0.,0.,1.));
#34=IFCCARTESIANPOINT('Storey Origin',(0.,0.,0.));
#35=IFCDIRECTION('Storey X',(1.,0.,0.));
#36=IFCDIRECTION('Storey Y',(0.,1.,0.));

#37=IFCSPACE('{space1_id}','Living Room','Living Room Description',$,#38,$,$,$,.ELEMENT.,$);
#38=IFCLOCALPLACEMENT(#39,#40);
#39=IFCAXIS2PLACEMENT3D(#41,#42,#43);
#40=IFCDIRECTION('Z',(0.,0.,1.));
#41=IFCCARTESIANPOINT('Room1 Origin',(0.,0.,0.));
#42=IFCDIRECTION('Room1 X',(1.,0.,0.));
#43=IFCDIRECTION('Room1 Y',(0.,1.,0.));

#44=IFCSPACE('{space2_id}','Bedroom','Bedroom Description',$,#45,$,$,$,.ELEMENT.,$);
#45=IFCLOCALPLACEMENT(#46,#47);
#46=IFCAXIS2PLACEMENT3D(#48,#49,#50);
#47=IFCDIRECTION('Z',(0.,0.,1.));
#48=IFCCARTESIANPOINT('Room2 Origin',(5.,0.,0.));
#49=IFCDIRECTION('Room2 X',(1.,0.,0.));
#50=IFCDIRECTION('Room2 Y',(0.,1.,0.));

#51=IFCSPACE('{space3_id}','Bathroom','Bathroom Description',$,#52,$,$,$,.ELEMENT.,$);
#52=IFCLOCALPLACEMENT(#53,#54);
#53=IFCAXIS2PLACEMENT3D(#55,#56,#57);
#54=IFCDIRECTION('Z',(0.,0.,1.));
#55=IFCCARTESIANPOINT('Room3 Origin',(0.,3.,0.));
#56=IFCDIRECTION('Room3 X',(1.,0.,0.));
#57=IFCDIRECTION('Room3 Y',(0.,1.,0.));

#58=IFCWALL('{wall1_id}','Wall 1','Wall 1 Description',$,#59,$,$,$);
#59=IFCLOCALPLACEMENT(#60,#61);
#60=IFCAXIS2PLACEMENT3D(#62,#63,#64);
#61=IFCDIRECTION('Z',(0.,0.,1.));
#62=IFCCARTESIANPOINT('Wall1 Origin',(0.,0.,0.));
#63=IFCDIRECTION('Wall1 X',(1.,0.,0.));
#64=IFCDIRECTION('Wall1 Y',(0.,1.,0.));

#65=IFCWALL('{wall2_id}','Wall 2','Wall 2 Description',$,#66,$,$,$);
#66=IFCLOCALPLACEMENT(#67,#68);
#67=IFCAXIS2PLACEMENT3D(#69,#70,#71);
#68=IFCDIRECTION('Z',(0.,0.,1.));
#69=IFCCARTESIANPOINT('Wall2 Origin',(10.,0.,0.));
#70=IFCDIRECTION('Wall2 X',(0.,1.,0.));
#71=IFCDIRECTION('Wall2 Y',(-1.,0.,0.));

#72=IFCWINDOW('{window1_id}','Window 1','Window 1 Description',$,#73,$,$,$);
#73=IFCLOCALPLACEMENT(#74,#75);
#74=IFCAXIS2PLACEMENT3D(#76,#77,#78);
#75=IFCDIRECTION('Z',(0.,0.,1.));
#76=IFCCARTESIANPOINT('Window1 Origin',(2.,0.,1.));
#77=IFCDIRECTION('Window1 X',(1.,0.,0.));
#78=IFCDIRECTION('Window1 Y',(0.,1.,0.));

#79=IFCDOOR('{door1_id}','Door 1','Door 1 Description',$,#80,$,$,$);
#80=IFCLOCALPLACEMENT(#81,#82);
#81=IFCAXIS2PLACEMENT3D(#83,#84,#85);
#82=IFCDIRECTION('Z',(0.,0.,1.));
#83=IFCCARTESIANPOINT('Door1 Origin',(5.,0.,0.));
#84=IFCDIRECTION('Door1 X',(1.,0.,0.));
#85=IFCDIRECTION('Door1 Y',(0.,1.,0.));

ENDSEC;

END-ISO-10303-21;'''.format(
        filename=filename,
        timestamp=datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        project_id='1P1K1Q1R1S1T1U1V1W1X1Y1Z',
        rel_id='1R1S1T1U1V1W1X1Y1Z1A1B1C1D',
        agg_id='1A1B1C1D1E1F1G1H1I1J1K1L1M',
        building_id='1B1C1D1E1F1G1H1I1J1K1L1M1N',
        site_id='1S1T1U1V1W1X1Y1Z1A1B1C1D1E1F',
        storey_id='1S1T1U1V1W1X1Y1Z1A1B1C1D1E1F1G',
        space1_id='1S1P1A1C1E1_1L1I1V1I1N1G1R1O1O1M',
        space2_id='1S1P1A1C1E1_1B1E1D1R1O1O1M',
        space3_id='1S1P1A1C1E1_1B1A1T1H1R1O1O1M',
        wall1_id='1W1A1L1L1_1N1O1R1T1H1_1W1A1L1L',
        wall2_id='1W1A1L1L1_1S1O1U1T1H1_1W1A1L1L',
        window1_id='1W1I1N1D1O1W1_1L1I1V1I1N1G1R1O1O1M',
        door1_id='1D1O1O1R1_1L1I1V1I1N1G1R1O1O1M'
    )
    
    # Записываем файл
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(ifc_content)
    
    print(f"✅ Создан тестовый IFC файл: {filename}")
    print(f"📏 Размер файла: {os.path.getsize(filename)} байт")
    
    return filename

def create_test_parameters():
    """Возвращает параметры тестовой модели"""
    return {
        "name": "Тестовая квартира",
        "area": 50.0,  # м²
        "rooms": 2,
        "bathrooms": 1,
        "windows": 1,
        "doors": 1,
        "walls": 2,
        "description": "Простая тестовая модель для проверки конвертации 3D → 2D",
        "expected_output": "2D чертеж с планом квартиры, размерами и аннотациями"
    }

if __name__ == "__main__":
    print("🏗️ Создание тестовой IFC модели")
    print("=" * 40)
    
    # Создаем тестовый файл
    filename = create_test_ifc_file()
    
    # Показываем параметры
    params = create_test_parameters()
    print(f"\n📋 Параметры тестовой модели:")
    for key, value in params.items():
        print(f"   {key}: {value}")
    
    print(f"\n🎯 Готово! Файл {filename} готов для тестирования.")
    print(f"📤 Загрузите его через кнопку 'Тест 3D→2D' в боте или API.")
