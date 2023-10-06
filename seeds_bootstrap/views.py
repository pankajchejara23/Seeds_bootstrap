from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site

from register import views as rv

from django.http import HttpResponseRedirect
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils import translation
from django.shortcuts import redirect
from django.core.paginator import Paginator
from register import forms as reg_forms
from django.contrib.sessions.models import Session
from .models import Scenario, TechGeneration, TechStorage, ScenarioLocation, Project
from .models import EnergySupply, EnergyTransmission, Vote, UserScenario, Electrification
import pandas as pd
import pprint as pp
import json

# param configurations
param_config = {'battery': {'max': 0.0444797482359873, 'min': 2.6183049409038122e-08},
                'bio': {'max': 1.0009737770934894, 'min': 4.134278090390732e-06},
                'freshwater_eutrophication': {'max': 1447977268.6580737,
                                              'min': 40539809.033321954},
                'global_warming': {'max': 3550705057804.7417, 'min': 89357470400.92726},
                'hydro_run_of_river': {'max': 1.6155, 'min': 1.6155},
                'import': {'max': 0.1561112495614454, 'min': 0.0003012119877652},
                'import_dep': {'max': 0.1561112495614454, 'min': 0.0003012119877652},
                'infra': {'max': 1.0, 'min': 0.1881200008807587},
                'land_occupation': {'max': 216513993113.64584, 'min': 20280814758.748016},
                'open_field_pv': {'max': 121.84232420443844, 'min': 2.231546741630743},
                'pace': {'max': 13.096833998642731, 'min': 3.729211861614511},
                'power': {'max': 159.63839465280677, 'min': 40.8581235544374},
                'roof_mounted_pv': {'max': 31.87839696159167, 'min': 0.0006874053401419},
                'scenario': {'max': 260.0, 'min': 0.0},
                'storage': {'max': 6.303784879568456, 'min': 5.898367317341074},
                'surplus_ore': {'max': 655458310608.2251, 'min': 9926424157.968464},
                'water_consumption': {'max': 61979898600.96115, 'min': 859061013.8176432},
                'wind_offshore': {'max': 12.2881549166774, 'min': 0.003085515351798},
                'wind_onshore': {'max': 44.36655376398457, 'min': 1.5571043872453}}

POWER_TECHS = ['chp_biofuel_extraction',
               'chp_hydrogen',
               'chp_methane_extraction',
               'chp_wte_back_pressure',
               'electrolysis',
               'existing_pv',
               'existing_wind',
               'hydro_reservoir',
               'hydro_run_of_river',
               'open_field_pv',
               'pumped_hydro',
               'wind_onshore',
               'battery',
               'ccgt',
               'roof_mounted_pv',
               'wind_offshore']


def map(request):
    return render(request, 'map.html')


def reduce_intensity(c, intensity=.2):
    return c.replace('0.8', '0.2')


def index(request):
    if request.method == "POST":
        return rv.login(request)
    else:
        form = reg_forms.LoginForm()
        return render(request, 'index.html', {'form': form})


def project_page(request):
    projects = Project.objects.all()
    return render(request, 'project_page.html', {'projects': projects})


def rescale(value, min, max):
    range = max - min
    return min + float(value) * range


def standardise(value, min, max):
    range = float(max) - float(min)
    return (float(value) - float(min)) / range


def interface(request, project_id):
    if request.method == 'POST':
        # fetching energy systems params
        power_min = request.POST['power_0']
        power_max = request.POST['power_1']
        storage_min = request.POST['storage_0']
        storage_max = request.POST['storage_1']

        community_min = rescale(
            float(request.POST['community_0']), param_config['infra']['min'], param_config['infra']['max'])
        community_max = rescale(
            float(request.POST['community_1']), param_config['infra']['min'], param_config['infra']['max'])
        implementation_min = request.POST['implement_0']
        implementation_max = request.POST['implement_1']
        import_min = rescale(
            float(request.POST['import_0']), param_config['import']['min'], param_config['import']['max'])
        import_max = rescale(
            float(request.POST['import_1']), param_config['import']['min'], param_config['import']['max'])

        ele_heat_min = request.POST['heat_0']
        ele_heat_max = request.POST['heat_1']

        ele_road_min = request.POST['transport_0']
        ele_road_max = request.POST['transport_1']

        # fetching impact controls params
        land_min = rescale(request.POST['land_0'], param_config['land_occupation']
                           ['min'], param_config['land_occupation']['max'])
        land_max = rescale(request.POST['land_1'], param_config['land_occupation']
                           ['min'], param_config['land_occupation']['max'])
        global_min = rescale(request.POST['global_0'], param_config['global_warming']
                             ['min'], param_config['global_warming']['max'])
        global_max = rescale(request.POST['global_1'], param_config['global_warming']
                             ['min'], param_config['global_warming']['max'])
        water_min = rescale(request.POST['water_0'], param_config['water_consumption']
                            ['min'], param_config['water_consumption']['max'])
        water_max = rescale(request.POST['water_1'], param_config['water_consumption']
                            ['min'], param_config['water_consumption']['max'])

        fresh_min = rescale(request.POST['fresh_0'], param_config['freshwater_eutrophication']
                            ['min'], param_config['freshwater_eutrophication']['max'])
        fresh_max = rescale(request.POST['fresh_1'], param_config['freshwater_eutrophication']
                            ['min'], param_config['freshwater_eutrophication']['max'])

        surplus_min = rescale(
            request.POST['surplus_0'], param_config['surplus_ore']['min'], param_config['surplus_ore']['max'])
        surplus_max = rescale(
            request.POST['surplus_1'], param_config['surplus_ore']['min'], param_config['surplus_ore']['max'])

        # fetching energy technologies params
        photo_roof_min = rescale(
            request.POST['photo-roof_0'], param_config['roof_mounted_pv']['min'], param_config['roof_mounted_pv']['max'])
        photo_roof_max = rescale(
            request.POST['photo-roof_1'], param_config['roof_mounted_pv']['min'], param_config['roof_mounted_pv']['max'])
        photo_open_field_min = rescale(
            request.POST['photo-open-field_0'], param_config['open_field_pv']['min'], param_config['open_field_pv']['max'])
        photo_open_field_max = rescale(
            request.POST['photo-open-field_1'], param_config['open_field_pv']['min'], param_config['open_field_pv']['max'])

        # @todo: add hydrogen in scenario table
        hydrogen_min = request.POST['hydrogen_0']
        hydrogen_max = request.POST['hydrogen_1']

        """
        hydro_river_min = request.POST['hydro-river_0']
        hydro_river_max = request.POST['hydro-river_1']
        hydro_pumped_min = request.POST['hydro-pumped_0']
        hydro_pumped_max = request.POST['hydro-pumped_1']
        hydro_reservoir_min = request.POST['hydro-reservoir_0']
        hydro_reservoir_max = request.POST['hydro-reservoir_1']
        """

        wind_on_shore_min = rescale(
            request.POST['wind-on-shore_0'], param_config['wind_onshore']['min'], param_config['wind_onshore']['max'])
        wind_on_shore_max = rescale(
            request.POST['wind-on-shore_1'], param_config['wind_onshore']['min'], param_config['wind_onshore']['max'])
        wind_off_shore_min = rescale(
            request.POST['wind-off-shore_0'], param_config['wind_offshore']['min'], param_config['wind_offshore']['max'])
        wind_off_shore_max = rescale(
            request.POST['wind-off-shore_1'], param_config['wind_offshore']['min'], param_config['wind_offshore']['max'])

        transmission_min = request.POST['transmission_0']
        transmission_max = request.POST['transmission_1']
        bio_min = request.POST['bio_0']
        bio_max = request.POST['bio_1']
        battery_min = rescale(
            request.POST['battery_0'], param_config['battery']['min'], param_config['battery']['max'])

        battery_max = rescale(
            request.POST['battery_1'], param_config['battery']['min'], param_config['battery']['max'])

        # print('Power min:{} max:{}'.format(power_min,power_max))
        # print('Hyodro-river min:{} max:{}'.format(hydro_river_min,hydro_river_max))
        # print('wind-on-shore min:{} max:{}'.format(wind_on_shore_min,wind_on_shore_max))
        # print('Human min:{} max:{}'.format(human_min,human_max))

        # Scale of parameters in database
        scenarios_community = Scenario.objects.all().filter(
            community_infrastructure__range=(community_min, community_max))
        print('community objects:', len(scenarios_community))
        scenarios_power = scenarios_community.filter(
            power_capacity__range=(power_min, power_max))
        print('power objects:', len(scenarios_power))
        scenarios_storage = scenarios_power.filter(
            storage_capacity__range=(storage_min, storage_max))
        print('storage objects:', len(scenarios_storage))
        scenarios_implementation = scenarios_storage.filter(
            implementation_pace__range=(implementation_min, implementation_max))
        print('impl objects:', len(scenarios_implementation))
        scenarios_import = scenarios_implementation.filter(
            import_dependency__range=(import_min, import_max)).order_by('id')

        scenarios_land = scenarios_import.filter(
            land_occupation__range=(land_min, land_max)).order_by('id')
        print('land objects:', len(scenarios_land))
        scenarios_global = scenarios_land.filter(
            global_warming__range=(global_min, global_max)).order_by('id')
        print('global objects:', len(scenarios_global))
        scenarios_surplus = scenarios_global.filter(
            surplus_ore__range=(surplus_min, surplus_max)).order_by('id')
        print('human objects:', len(scenarios_surplus))
        scenarios_water = scenarios_surplus.filter(
            water_consumption__range=(water_min, water_max)).order_by('id')

        scenarios_fresh = scenarios_water.filter(
            freshwater_eutrophication__range=(fresh_min, fresh_max)).order_by('id')

        # scenarios_implementation = scenarios_storage
        paginator = Paginator(scenarios_land, 20, orphans=3)
        page_obj = paginator.get_page(1)
        page_range = list(paginator.get_elided_page_range(1))
        print('Final objects:', len(scenarios_land))
        return render(request, 'show_results.html', {'page_obj': page_obj, 'page_range': page_range})
    else:
        locations = ScenarioLocation.objects.all()
        return render(request, 'param_selection.html', {'locations': locations})


def get_scenario_details(scenario_id):
    data = {}
    scenario = Scenario.objects.get(id=scenario_id)
    tech_sto = TechStorage.objects.all().filter(scenario=scenario)
    tech_gen = TechGeneration.objects.all().filter(scenario=scenario)
    energy = EnergySupply.objects.all().filter(scenario=scenario)
    electrification = Electrification.objects.all().filter(scenario=scenario)
    transmission = EnergyTransmission.objects.all().filter(scenario=scenario)

    data['storage'] = {}
    data['generation'] = {}
    data['energy'] = {}
    data['electrification'] = {}
    data['transmission'] = {}

    radial_chart_r = [scenario.land_occupation, scenario.global_warming,
                      scenario.water_consumption, scenario.surplus_ore, scenario.freshwater_eutrophication]
    radial_chart_theta = ['Land Occupation', 'Global Warming',
                          'Water Consumption', 'Surplus Ore', 'FreshWater Eutrophication']
    # data for bar chart of power generation

    impact_names = [('_'.join(item.split(' '))).lower()
                    for item in radial_chart_theta]

    tmp = []
    for ind, val in enumerate(radial_chart_r):
        print(param_config[impact_names[ind]]['min'],
              param_config[impact_names[ind]]['max'])
        tmp.append(standardise(
            val, param_config[impact_names[ind]]['min'], param_config[impact_names[ind]]['max']))

    data['radial_r'] = tmp
    data['radial_theta'] = radial_chart_theta

    bar_chart_data = []

    total_hydro = 0

    total_generation = 0
    for ob in tech_gen:
        data['generation'][ob.technology_type] = ob.energy_generation
        total_generation += ob.energy_generation
        trace = {
            "y": ['Power'],
            "x": [int(ob.energy_generation)],
            "name": ob.technology_type,
            "type": 'bar',
            "orientation": 'h'
        }
        bar_chart_data.append(trace)
        if 'hydro_' in ob.technology_type:
            total_hydro += ob.energy_generation

    data['power_bar_data'] = bar_chart_data

    pie_chart_data = {}
    pie_values = {}

    total_storage = 0

    for ob in tech_sto:
        data['storage'][ob.technology_type] = ob.energy_storage
        if ob.energy_storage in pie_values.keys():
            pie_values[ob.technology_type] += float(ob.energy_storage)
        else:
            pie_values[ob.technology_type] = float(ob.energy_storage)

        total_storage += ob.energy_storage

    pie_chart_data['labels'] = list(pie_values.keys())
    pie_chart_data['values'] = list(pie_values.values())
    # data manipulation to create half pie
    count_storage_tech = len(pie_chart_data['labels'])
    sum_storage = sum(pie_chart_data['values'])

    # pie_chart_data['values'] = [item/count_storage_tech for item in pie_chart_data['values']]
    pie_chart_data['values'].append(float(pie_chart_data['values'][0]))
    pie_chart_data['labels'].append('a')

    data['power_pie_data'] = pie_chart_data

    total_supply = 0
    for ob in energy:
        data['energy']['technology_type'] = ob.energy_supply
        total_supply += ob.energy_supply

    total_electrification = 0
    for ob in electrification:
        data['electrification']['type'] = ob.carriers_type
        data['electrification']['value'] = ob.electrification_rate
        total_electrification += ob.electrification_rate

    total_transmission = 0
    for ob in transmission:
        data['transmission']['from'] = ob.from_location
        data['transmission']['to'] = ob.to_location
        data['transmission']['transmission'] = ob.transmission_capacity
        total_transmission += ob.transmission_capacity

    data['total_storage'] = total_storage
    data['total_supply'] = total_supply
    data['total_electrification'] = total_electrification
    data['total_transmission'] = total_transmission
    data['total_hydro'] = total_hydro
    data['total_generation'] = total_generation
    if scenario.roof_mounted_pv:
        roof = scenario.roof_mounted_pv
    else:
        roof = 0
    if scenario.open_field_pv:
        open = scenario.open_field_pv
    else:
        open = 0
    data['total_pv'] = roof + open

    if scenario.wind_onshore:
        onshore = scenario.wind_onshore
    else:
        onshore = 0

    if scenario.wind_offshore:
        offshore = scenario.wind_offshore
    else:
        offshore = 0
    data['total_wind'] = onshore + offshore

    return data


def get_energy_supply(scenario_id):

    scenario = Scenario.objects.get(id=scenario_id)
    supply = EnergySupply.objects.all().filter(scenario=scenario)

    energy = {}

    for ob in supply:
        energy[ob.technology_type] = float(ob.energy_supply)

    print(energy)

    return energy


def get_sankey_data(scenario_id):
    available_color_code_index = 0
    data = get_scenario_details(scenario_id)

    nodes_labels = [item for item in data['impact'].keys()]
    nodes_labels += ['land_occupation', 'marine_toxicity',
                     'human_toxicity', 'metal_depletion',
                     'fossil_depletion', 'total']

    nodes_color = {}
    for key in nodes_labels:
        nodes_color[key] = COLOR_CODES[available_color_code_index]
        available_color_code_index += 1

    link = []

    for key in data['impact'].keys():

        link.append({'source': 'total',
                     'target': key,
                     'color': reduce_intensity(nodes_color[key]),
                     'value': sum(list(data['impact'][key].values()))
                     })

        for impact_type, impact_value in data['impact'][key].items():

            link.append({'source': key,
                         'target': impact_type,
                         'color': reduce_intensity(nodes_color[impact_type]),
                         'value': impact_value
                         })
    source = []
    target = []
    link_value = []
    link_color = []

    for l in link:
        source.append(nodes_labels.index(l['source']))
        target.append(nodes_labels.index(l['target']))
        link_value.append(float(l['value']))
        link_color.append(l['color'])

    return {'data': data,
            'scenario': scenario_id,
            'nodes': nodes_labels, 'source': source,
            'target': target, 'value': link_value,
            'nodes_color': list(nodes_color.values()),
            'link_color': link_color}


def compare(request):
    scenario_id_1 = 18
    scenario_id_2 = 27
    template_data1 = get_sankey_data(scenario_id_1)
    template_data2 = get_sankey_data(scenario_id_2)
    return render(request, 'compare_scenario.html', {'template_data1': template_data1,
                                                     'template_data2': template_data2})


def inspect(request, scenario_id):
    scenario = Scenario.objects.get(id=scenario_id)
    data = get_scenario_details(scenario_id)
    sup = get_energy_supply(scenario_id)
    data['scenario'] = scenario
    if request.method == 'POST':
        scenario = Scenario.objects.get(id=scenario_id)
        label = request.POST['label']
        user = request.user
        project = Project.objects.get(id=request.session['project'])
        obj = UserScenario.objects.create(
            submitted_user=user, label=label, project=project, scenario=scenario)
        print('Object saved', obj)
        request.session['selected_location'] = str(select_location)
        messages.success(request, "Scenario has been added to your portfolio")
        return render(request, 'inspect_scenario.html', {'data': data})
    else:
        return render(request, 'inspect_scenario.html', {'data': data})


def select_location(request):
    locations = ScenarioLocation.objects.all()
    if request.method == 'POST':
        selected_location = request.POST['location']
        print(selected_location)
        request.session['selected_location'] = str(select_location)
        return redirect('interface')
    else:
        return render(request, 'select_location_page.html', {'locations': locations})


def aboutus(request):
    return render(request, 'index.html', {})


def vote(request, selection, scenario):
    project_obj = Project.objects.get(id=request.session['project'])
    response = True if selection == 'up' else False
    submitted_user = request.user
    scenario_obj = Scenario.objects.get(id=scenario)

    obj = Vote(project=project_obj, response=response,
               submitted_user=submitted_user, scenario=scenario_obj)
    obj.save()
    messages.success(request, "Your vote has been saved")
    return redirect('inspect', scenario_id=scenario)


def portfolio(request):

    scenarios = UserScenario.objects.all().filter(submitted_user=request.user)
    return render(request, 'portfolio.html', {'scenarios': scenarios})
