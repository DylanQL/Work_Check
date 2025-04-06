from django.shortcuts import render, redirect
from functools import wraps
from django.contrib import messages
from .models import *

# Decorador personalizado para verificar que el usuario haya iniciado sesión
def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not request.session.get('user_id'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapped_view

# Vista de Login
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username').strip()
        password = request.POST.get('password').strip()
        try:
            user_account = UserAccount.objects.get(username=username, password=password)
            if user_account.status != "Activo":
                error = "La cuenta no está activa."
                return render(request, 'System/login.html', {'error': error})
            request.session['user_id'] = user_account.id
            return redirect('home')
        except UserAccount.DoesNotExist:
            error = "Credenciales inválidas."
            return render(request, 'System/login.html', {'error': error})
    return render(request, 'System/login.html')

# Vista para cerrar sesión
def logout_view(request):
    request.session.flush()
    return redirect('login')

# Vista principal (acceso restringido)
@login_required
def home(request):
    return render(request, 'System/home.html')

# Nueva vista para gestionar usuarios (lista de usuarios)
@login_required
def manage_users(request):
    usuarios = Usuario.objects.all()
    return render(request, 'System/manage_users.html', {'usuarios': usuarios})


# Vista para agregar usuarios
@login_required
def add_user(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name').strip()
        middle_name = request.POST.get('middle_name', '').strip()
        last_name = request.POST.get('last_name').strip()
        second_last_name = request.POST.get('second_last_name', '').strip()
        user_type = request.POST.get('user_type').strip()
        position_id = request.POST.get('position')
        
        # Se crea el registro en la tabla Usuario
        usuario = Usuario.objects.create(
            first_name=first_name,
            middle_name=middle_name if middle_name != '' else None,
            last_name=last_name,
            second_last_name=second_last_name if second_last_name != '' else None,
            user_type=user_type,
            position_id=position_id
        )
        
        # Se crea automáticamente el registro en la tabla TimeSheetScore con score_ts=0
        TimeSheetScore.objects.create(
            usuario=usuario,
            score_ts=0
        )
        
        # Se genera el username concatenando first_name, last_name y second_last_name (si existe), en minúsculas sin espacios
        username = (first_name + last_name + (second_last_name if second_last_name else '')).replace(" ", "").lower()
        default_password = "123456"
        
        # Se crea el registro en la tabla UserAccount
        UserAccount.objects.create(
            username=username,
            password=default_password,
            usuario=usuario,
            status="Activo"
        )
        
        return redirect('home')
    
    positions = Position.objects.all()
    return render(request, 'System/add_user.html', {'positions': positions})

# Vista para actualizar usuarios
@login_required
def update_user(request, user_id):
    try:
        usuario = Usuario.objects.get(id=user_id)
    except Usuario.DoesNotExist:
        return redirect('home')
    
    if request.method == 'POST':
        usuario.first_name = request.POST.get('first_name').strip()
        usuario.middle_name = request.POST.get('middle_name', '').strip() or None
        usuario.last_name = request.POST.get('last_name').strip()
        usuario.second_last_name = request.POST.get('second_last_name', '').strip() or None
        usuario.user_type = request.POST.get('user_type').strip()
        usuario.position_id = request.POST.get('position')
        usuario.save()
        
        # Actualización opcional del username en UserAccount
        username = (usuario.first_name + usuario.last_name + (usuario.second_last_name if usuario.second_last_name else '')).replace(" ", "").lower()
        user_account = UserAccount.objects.get(usuario=usuario)
        user_account.username = username
        user_account.save()
        
        return redirect('home')
    
    positions = Position.objects.all()
    return render(request, 'System/update_user.html', {'usuario': usuario, 'positions': positions})


# Vista para listar las cuentas (gestión de UserAccount)
@login_required
def list_accounts(request):
    accounts = UserAccount.objects.all()
    return render(request, 'System/manage_accounts.html', {'accounts': accounts})

# Vista para actualizar una cuenta existente
@login_required
def update_account(request, account_id):
    try:
        account = UserAccount.objects.get(id=account_id)
    except UserAccount.DoesNotExist:
        return redirect('list_accounts')
    
    if request.method == 'POST':
        account.username = request.POST.get('username').strip()
        account.password = request.POST.get('password').strip()
        account.status = request.POST.get('status').strip()
        account.save()
        return redirect('list_accounts')
    
    return render(request, 'System/update_account.html', {'account': account})

# Vista para listar los Timesheet Scores
@login_required
def list_timesheets(request):
    timesheets = TimeSheetScore.objects.all()
    return render(request, 'System/manage_timesheets.html', {'timesheets': timesheets})

# Vista para actualizar un Timesheet Score
@login_required
def update_timesheet(request, timesheet_id):
    try:
        timesheet = TimeSheetScore.objects.get(id=timesheet_id)
    except TimeSheetScore.DoesNotExist:
        return redirect('list_timesheets')
    
    if request.method == 'POST':
        score_value = request.POST.get('score_ts').strip()
        try:
            timesheet.score_ts = int(score_value)
        except ValueError:
            error = "El valor debe ser un número entero."
            return render(request, 'System/update_timesheet.html', {'timesheet': timesheet, 'error': error})
        timesheet.save()
        return redirect('list_timesheets')
    
    return render(request, 'System/update_timesheet.html', {'timesheet': timesheet})

# Vista para listar los ciclos de evaluación
@login_required
def list_evaluation_cycles(request):
    cycles = EvaluationCycle.objects.all()
    return render(request, 'System/manage_evaluation_cycles.html', {'cycles': cycles})

# Vista para crear un nuevo ciclo de evaluación
@login_required
def create_evaluation_cycle(request):
    if request.method == 'POST':
        name = request.POST.get('name').strip()
        if name:
            EvaluationCycle.objects.create(name=name)
            return redirect('list_evaluation_cycles')
        else:
            error = "El nombre es requerido."
            return render(request, 'System/create_evaluation_cycle.html', {'error': error})
    return render(request, 'System/create_evaluation_cycle.html')

# Vista para actualizar un ciclo de evaluación existente
@login_required
def update_evaluation_cycle(request, cycle_id):
    try:
        cycle = EvaluationCycle.objects.get(id=cycle_id)
    except EvaluationCycle.DoesNotExist:
        return redirect('list_evaluation_cycles')
    
    if request.method == 'POST':
        name = request.POST.get('name').strip()
        if name:
            cycle.name = name
            cycle.save()
            return redirect('list_evaluation_cycles')
        else:
            error = "El nombre es requerido."
            return render(request, 'System/update_evaluation_cycle.html', {'cycle': cycle, 'error': error})
    
    return render(request, 'System/update_evaluation_cycle.html', {'cycle': cycle})

# Vista para eliminar un ciclo de evaluación
@login_required
def delete_evaluation_cycle(request, cycle_id):
    try:
        cycle = EvaluationCycle.objects.get(id=cycle_id)
    except EvaluationCycle.DoesNotExist:
        return redirect('list_evaluation_cycles')
    
    if request.method == 'POST':
        cycle.delete()
        return redirect('list_evaluation_cycles')
    
    return render(request, 'System/delete_evaluation_cycle.html', {'cycle': cycle})

# Lista de asignaciones temporales (mostrar solo los registros existentes)
@login_required
def list_temp_evaluation_assignments(request):
    assignments = Temp_EvaluationAssignment.objects.all()
    return render(request, 'System/manage_temp_evaluation_assignments.html', {'assignments': assignments})

# Crear una nueva asignación de evaluación
@login_required
def create_temp_evaluation_assignment(request):
    # Filtrar evaluadores según user_type ("Lider" o "Gerente")
    evaluators = Usuario.objects.filter(user_type__in=["Lider", "Gerente"])
    # Filtrar empleados que sean "Empleado" y que aún no tengan asignación
    assigned_employee_ids = Temp_EvaluationAssignment.objects.values_list('employee_id', flat=True)
    allowed_employee_roles = ["Empleado", "Lider"]
    employees = Usuario.objects.filter(user_type__in=allowed_employee_roles).exclude(id__in=assigned_employee_ids)
    
    if request.method == 'POST':
        evaluator_id = request.POST.get('evaluator')
        employee_id = request.POST.get('employee')
        # Se asigna automáticamente el status "Pendiente"
        status = "Pendiente"
        
        if Temp_EvaluationAssignment.objects.filter(employee_id=employee_id).exists():
            error = "Ya existe una asignación para este empleado."
            return render(request, 'System/create_temp_evaluation_assignment.html', {
                'evaluators': evaluators,
                'employees': employees,
                'error': error
            })
        
        # Obtener el último EvaluationCycle para asignar evaluation_cycle
        last_cycle = EvaluationCycle.objects.order_by('-id').first()
        evaluation_cycle_value = last_cycle.name if last_cycle else ''
        
        Temp_EvaluationAssignment.objects.create(
            evaluator_id=evaluator_id,
            employee_id=employee_id,
            status=status,
            evaluation_cycle=evaluation_cycle_value
        )
        return redirect('list_temp_assignments')
    
    return render(request, 'System/create_temp_evaluation_assignment.html', {
        'evaluators': evaluators,
        'employees': employees
    })



# Actualizar una asignación de evaluación temporal
@login_required
def update_temp_evaluation_assignment(request, assignment_id):
    try:
        assignment = Temp_EvaluationAssignment.objects.get(id=assignment_id)
    except Temp_EvaluationAssignment.DoesNotExist:
        return redirect('list_temp_assignments')
    
    # Filtrar evaluadores según user_type ("Lider" o "Gerente")
    evaluators = Usuario.objects.filter(user_type__in=["Lider", "Gerente"])
    
    if request.method == 'POST':
        evaluator_id = request.POST.get('evaluator')
        # No se actualiza el status, que permanece "Pendiente"
        assignment.evaluator_id = evaluator_id
        assignment.save()
        return redirect('list_temp_assignments')
    
    return render(request, 'System/update_temp_evaluation_assignment.html', {
        'assignment': assignment,
        'evaluators': evaluators
    })



# Eliminar una asignación temporal (opcional, si se requiere)
@login_required
def delete_temp_evaluation_assignment(request, assignment_id):
    try:
        assignment = Temp_EvaluationAssignment.objects.get(id=assignment_id)
    except Temp_EvaluationAssignment.DoesNotExist:
        return redirect('list_temp_evaluation_assignments')
    
    if request.method == 'POST':
        assignment.delete()
        return redirect('list_temp_evaluation_assignments')
    
    return render(request, 'System/delete_temp_evaluation_assignment.html', {'assignment': assignment})

@login_required
def send_assignments_to_historic(request):
    """
    Envía los registros de Temp_EvaluationAssignment a Permanent_EvaluationAssignment,
    copiando el campo summary (ID del Summary) a la nueva instancia.
    Antes de enviar se verifica que todos los registros tengan status "Completado" y
    que cada asignación tenga un summary asociado.
    """
    assignments = Temp_EvaluationAssignment.objects.all()
    incomplete = assignments.exclude(status="Completado")
    if incomplete.exists():
        messages.error(request, "No todos los usuarios completaron sus evaluaciones.")
        return redirect('list_temp_assignments')
    
    if request.method == 'POST':
        for assign in assignments:
            if not assign.summary:
                messages.error(
                    request,
                    f"La asignación para el empleado {assign.employee.first_name} {assign.employee.last_name} no tiene summary asociado."
                )
                return redirect('list_temp_assignments')
            Permanent_EvaluationAssignment.objects.create(
                evaluator=assign.evaluator,
                employee=assign.employee,
                status=assign.status,
                evaluation_cycle=assign.evaluation_cycle,
                summary=assign.summary  # Se copia el registro de Summary
            )
        assignments.delete()
        messages.success(request, "Registros enviados a histórico correctamente.")
        return redirect('list_temp_assignments')
    
    return render(request, 'System/confirm_send_assignments.html', {})



# Vistas para mostrar los registros históricos (Permanent_EvaluationAssignment)
# y para mostrar el detalle de los registros de Summary y EvaluationDetails.

@login_required
def list_permanent_assignments(request):
    """
    Lista todos los registros históricos de evaluaciones permanentes.
    Se muestra una tabla con los registros; en los campos 'summary' y 'evaluation_details'
    se incluyen enlaces a la vista de detalle correspondiente si existe el registro.
    """
    assignments = Permanent_EvaluationAssignment.objects.all()
    return render(request, 'System/manage_permanent_assignments.html', {'assignments': assignments})

@login_required
def detail_summary(request, summary_id):
    """
    Muestra el detalle de un registro Summary.
    Si no se encuentra el registro, redirige a la lista de asignaciones permanentes.
    """
    try:
        summary = Summary.objects.get(id=summary_id)
    except Summary.DoesNotExist:
        return redirect('list_permanent_assignments')
    return render(request, 'System/detail_summary.html', {'summary': summary})

@login_required
def detail_evaluation_details(request, evaluation_details_id):
    """
    Muestra el detalle de un registro EvaluationDetails.
    Si el registro no existe, redirige a la lista de asignaciones permanentes.
    """
    try:
        details = EvaluationDetails.objects.get(id=evaluation_details_id)
    except EvaluationDetails.DoesNotExist:
        return redirect('list_permanent_assignments')
    return render(request, 'System/detail_evaluation_details.html', {'details': details})


@login_required
def leaders_evaluations(request):
    """
    Muestra las evaluaciones de líderes.
    
    Se filtran los registros de Permanent_EvaluationAssignment cuyo 
    Summary asociado tenga evaluation_type igual a "Lideres".
    De cada registro se muestra:
      - Desde Permanent_EvaluationAssignment: evaluation_cycle.
      - Desde Summary: employee, evaluator, R, L, H, E, C, M, V, final_score, performance_level y position.
    """
    assignments = Permanent_EvaluationAssignment.objects.filter(summary__evaluation_type="Lideres")
    return render(request, 'System/leaders_evaluations.html', {'assignments': assignments})

@login_required
def employees_evaluations(request):
    """
    Muestra las evaluaciones de empleados.
    
    Se filtran los registros de Permanent_EvaluationAssignment cuyo registro
    asociado de Summary tenga evaluation_type igual a "Empleados". De cada registro,
    se muestran:
      - Desde Permanent_EvaluationAssignment: evaluation_cycle.
      - Desde Summary: employee, evaluator, R, H, E, C, M, V, final_score,
        performance_level y position.
    """
    assignments = Permanent_EvaluationAssignment.objects.filter(summary__evaluation_type="Empleados")
    return render(request, 'System/employees_evaluations.html', {'assignments': assignments})



@login_required
def evaluation_form_view(request):
    """
    Vista para mostrar y procesar el Formulario de Evaluación.
    - Solo aparecen usuarios (employee) con status "Pendiente" asignados al usuario logueado (evaluator).
    - Al enviar, se crea un registro en EvaluationDetails y Summary.
    - Se actualiza el campo summary en Temp_EvaluationAssignment con el ID del Summary creado.
    """
    # 1. Identificar al usuario logueado
    user_account_id = request.session.get('user_id')
    # Obtener el usuario (evaluator) asociado a esa cuenta
    # Asumiendo que tienes un modelo UserAccount que relaciona con Usuario
    from .models import UserAccount  
    try:
        user_account = UserAccount.objects.get(id=user_account_id)
        evaluator_usuario = user_account.usuario
    except UserAccount.DoesNotExist:
        return redirect('logout')

    # 2. Obtener los empleados asignados al usuario logueado con status "Pendiente"
    #    (Temp_EvaluationAssignment)
    assignments = Temp_EvaluationAssignment.objects.filter(
        evaluator=evaluator_usuario,
        status="Pendiente"
    )

    # Obtener la lista de usuarios (employee) y sus posiciones
    # para rellenar el select y luego actualizar dinámicamente la posición
    employees_data = []
    for a in assignments:
        emp = a.employee
        employees_data.append({
            'id': emp.id,
            'nombre': f"{emp.first_name} {emp.last_name}",
            'position': emp.position.position_name  # se asume que emp.position existe
        })

    if request.method == 'POST':
        # 3. Procesar el envío del formulario
        #    a) Identificar al employee seleccionado y la asignación
        employee_id = request.POST.get('employee_id')
        try:
            assignment = Temp_EvaluationAssignment.objects.get(
                evaluator=evaluator_usuario,
                employee_id=employee_id,
                status="Pendiente"
            )
        except Temp_EvaluationAssignment.DoesNotExist:
            messages.error(request, "No se encontró la asignación pendiente para ese usuario.")
            return redirect('evaluation_form')

        # b) Crear registro en EvaluationDetails con los campos R1..R5, L1..L5, etc.
        #    Parsear valores numéricos (pueden llegar como strings)
        def parse_int(value):
            try:
                return int(value)
            except:
                return 0

        R1 = parse_int(request.POST.get('R1'))
        R2 = parse_int(request.POST.get('R2'))
        R3 = parse_int(request.POST.get('R3'))
        R4 = parse_int(request.POST.get('R4'))
        R5 = parse_int(request.POST.get('R5'))
        R_comments = request.POST.get('R_comments', '')

        L1 = parse_int(request.POST.get('L1'))
        L2 = parse_int(request.POST.get('L2'))
        L3 = parse_int(request.POST.get('L3'))
        L4 = parse_int(request.POST.get('L4'))
        L5 = parse_int(request.POST.get('L5'))
        L_comments = request.POST.get('L_comments', '')

        H1 = parse_int(request.POST.get('H1'))
        H2 = parse_int(request.POST.get('H2'))
        H3 = parse_int(request.POST.get('H3'))
        H4 = parse_int(request.POST.get('H4'))
        H5 = parse_int(request.POST.get('H5'))
        H_comments = request.POST.get('H_comments', '')

        E1 = parse_int(request.POST.get('E1'))
        E2 = parse_int(request.POST.get('E2'))
        E3 = parse_int(request.POST.get('E3'))
        E4 = parse_int(request.POST.get('E4'))
        E_comments = request.POST.get('E_comments', '')

        C1 = parse_int(request.POST.get('C1'))
        C2 = parse_int(request.POST.get('C2'))
        C3 = parse_int(request.POST.get('C3'))
        C4 = parse_int(request.POST.get('C4'))
        C5 = parse_int(request.POST.get('C5'))
        C6 = parse_int(request.POST.get('C6'))
        C_comments = request.POST.get('C_comments', '')

        M1 = parse_int(request.POST.get('M1'))
        M2 = parse_int(request.POST.get('M2'))
        M_comments = request.POST.get('M_comments', '')

        V1 = parse_int(request.POST.get('V1'))
        V2 = parse_int(request.POST.get('V2'))
        V3 = parse_int(request.POST.get('V3'))
        V4 = parse_int(request.POST.get('V4'))
        V5 = parse_int(request.POST.get('V5'))
        V_comments = request.POST.get('V_comments', '')

        final_comments = request.POST.get('final_comments', '')

        # Crear EvaluationDetails
        evaluation_details = EvaluationDetails.objects.create(
            R1=R1, R2=R2, R3=R3, R4=R4, R5=R5, R_comments=R_comments,
            L1=L1, L2=L2, L3=L3, L4=L4, L5=L5, L_comments=L_comments,
            H1=H1, H2=H2, H3=H3, H4=H4, H5=H5, H_comments=H_comments,
            E1=E1, E2=E2, E3=E3, E4=E4, E_comments=E_comments,
            C1=C1, C2=C2, C3=C3, C4=C4, C5=C5, C6=C6, C_comments=C_comments,
            M1=M1, M2=M2, M_comments=M_comments,
            V1=V1, V2=V2, V3=V3, V4=V4, V5=V5, V_comments=V_comments,
            final_comments=final_comments
        )

        # c) Calcular promedios y final_score
        avg_R = (R1 + R2 + R3 + R4 + R5) / 5
        avg_L = (L1 + L2 + L3 + L4 + L5) / 5
        avg_H = (H1 + H2 + H3 + H4 + H5) / 5
        avg_E = (E1 + E2 + E3 + E4) / 4
        avg_C = (C1 + C2 + C3 + C4 + C5 + C6) / 6
        avg_M = (M1 + M2) / 2
        avg_V = (V1 + V2 + V3 + V4 + V5) / 5

        # Ponderaciones
        weighted_R = avg_R * 0.20
        weighted_L = avg_L * 0.20
        weighted_H = avg_H * 0.10
        weighted_E = avg_E * 0.10
        weighted_C = avg_C * 0.15
        weighted_M = avg_M * 0.15
        weighted_V = avg_V * 0.10

        final_score = weighted_R + weighted_L + weighted_H + weighted_E + weighted_C + weighted_M + weighted_V

        # d) Determinar performance_level según final_score
        if 1.0 <= final_score <= 1.99:
            performance_level = "Nivel 1"
        elif 2.0 <= final_score <= 2.74:
            performance_level = "Nivel 2"
        elif 2.75 <= final_score <= 3.49:
            performance_level = "Nivel 3"
        elif 3.5 <= final_score <= 4.49:
            performance_level = "Nivel 4"
        elif 4.5 <= final_score <= 5.0:
            performance_level = "Nivel 5"
        else:
            performance_level = "Fuera de rango"

        # e) Crear Summary
        #    Asumimos que evaluation_type podría ser "Empleados" o "Lideres". 
        #    Aquí podrías definir la lógica para setearlo según tu necesidad.
        #    Como no está especificado, usaremos "Empleados" a modo de ejemplo.
        summary_obj = Summary.objects.create(
            employee=assignment.employee,
            evaluator=assignment.evaluator,
            R=avg_R, L=avg_L, H=avg_H, E=avg_E, C=avg_C, M=avg_M, V=avg_V,
            final_score=final_score,
            performance_level=performance_level,
            evaluation_type="Empleados",  # o "Lideres" según corresponda
            position=assignment.employee.position,
            evaluation_details=evaluation_details
        )

        # f) Actualizar Temp_EvaluationAssignment con el summary recién creado
        assignment.summary = summary_obj
        # (Opcional) Cambiar el status a "Completado"
        assignment.status = "Completado"
        assignment.save()

        messages.success(request, "Evaluación guardada exitosamente.")
        return redirect('evaluation_form')

    # GET: mostrar el formulario
    return render(request, 'System/evaluation_form.html', {
        'employees_data': employees_data
    })
