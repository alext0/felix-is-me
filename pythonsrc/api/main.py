from flask import g
from datetime import datetime

from util.api_util import not_found
from util.json_util import jsonify
from api import api
from util.api_util import Location, bad_request
from marshmallow import missing
from webargs import fields
from webargs.flaskparser import use_kwargs
from util.access_util import login_required, project_owner_required


@api.route('/main', methods=['GET'])
@login_required
@use_kwargs({'section_id':fields.Int(), 'owner_user_id': fields.Int()}, locations=Location.query)
def get_projects(section_id, owner_user_id):
    """
    ---
    get:
        description: Return a list of projects.

        parameters:
            - name: section_id
              description: ID of the section you want the results filtered by.
              in: query
              type: integer
            - name: owner_user_id
              description: ID of the user you want the results filtered by.
              in: query
              type: integer

        responses:
            200:
                description: List of projects.
                schema:
                    type: array
                    items: ProjectSchema

    """

    query = db.session.query(Project)\
        .outerjoin(Cdh).options(db.contains_eager(Project.cdh))\
        .outerjoin(Clustering).options(db.contains_eager(Project.clustering))\
        .outerjoin(TaskState).options(db.contains_eager(Project.task_state))\
        .outerjoin(Task).options(db.contains_eager(Project.task_state).contains_eager(TaskState.task))\
        .join(User).options(db.contains_eager(Project.owner_user))

    if section_id:
        query = query.filter(Cdh.section_id == section_id)

    if owner_user_id:
        query = query.filter(Project.owner_user_id == owner_user_id)

    query = query.order_by(Project.id, Task.workflow_order)

    return get_all(query, ProjectSchema, exclude = ['decisions', 'section'])


@api.route('/projects/<int:project_id>', methods=['GET'])
@login_required
def get_project(project_id):
    """
    ---
    get:
        description: Get project.

        parameters:
            - name: project_id
              description: Project ID
              in: path
              type: integer

        responses:
            200:
                description: Project
                schema: ProjectSchema
    """

    task_alias = db.aliased(Task)

    return get_one(db.session.query(Project)
                   .filter(Project.id == project_id)
                   .outerjoin(TaskState)
                   .outerjoin(Task)
                   .outerjoin(Clustering)
                   .outerjoin(task_alias, task_alias.id == Project.current_task_id)
                   .options(db.contains_eager(Project.task_state))
                   .options(db.contains_eager(Project.current_task, alias=task_alias))
                   .options(db.contains_eager(Project.task_state).contains_eager(TaskState.task))
                   .options(db.contains_eager(Project.clustering))
                   .order_by(Task.workflow_order), ProjectSchema, exclude=['cdh', 'decisions', 'owner_user', 'section'])


@api.route('/projects/<int:project_id>/task_complete', methods=['POST'])
@login_required
@project_owner_required
@use_kwargs({'task_name': fields.Str(required=True)}, locations=Location.json)
def set_task_complete(task_name, project_id):
    """
    ---
    post:
        description: Set a task as complete

        parameters:
            - name: project_id
              description: Project ID
              in: path
              required: true
              type: integer
            - name: task_name
              description: Name of the task that is complete
              in: body
              type: string

        responses:
            200:
                description: Task has been set as complete
            400:
                description: Task could not be set as complete
    """
    project = Project.query.filter(Project.id == project_id).first()

    # TODO: When we have other tasks this will need updating to check that they can build_branches based on the project state
    if task_name == 'build_branches':
        project.delete_branch_skus()

        cdh_item_branches = db.session.query(CdhItemMember).filter(CdhItemMember.project_id == project.id)
        for cdh_item_branch in cdh_item_branches:
            if cdh_item_branch.cdh_item_id:
                project.map_skus_to_branches(cdh_item_branch.cdh_item_id, cdh_item_branch.branch_id)

            if cdh_item_branch.cdh_item_sku_id:
                cdh_item_sku = db.session.query(CdhItemSku).filter(
                    CdhItemSku.id == cdh_item_branch.cdh_item_sku_id).first()

                db.session.add(BranchSku(
                    branch_id=cdh_item_branch.branch_id,
                    cdh_id=project.cdh_id,
                    sku_id=cdh_item_sku.sku_id
                ))

        db.session.flush()

        if project.has_mapped_all_cdh_items():
            db.session.commit()
            project.viewstate_for_cann_boundary_builder = project.viewstate_for_branch_builder
            project.copy_branches_to_cann_boundaries()
            project.assign_recommended_branch_quality_framework_classification_and_sales()

            project.complete_task('build_branches')

            db.session.commit()
            return '', 200
        else:
            db.session.rollback()
            message = {
                'message': 'Some CDH Items have not been mapped to a branch'
            }
            resp = jsonify(message)
            resp.status_code = 400

            return resp

    elif task_name == 'cann_boundaries' or task_name == 'strategic_guidance':

        task = db.session.query(Task).filter(Task.name == task_name).first()

        if project.current_task_id == task.id:
            project.complete_task(task_name)

            db.session.commit()
            return '', 200
        else:
            message = {
                'message': 'Cannot mark {} task as complete as it\'s not the current task.'.format(task_name)
            }
            resp = jsonify(message)
            resp.status_code = 400

            return resp

    message = {
        'message': 'Invalid task_name'
    }
    resp = jsonify(message)
    resp.status_code = 400

    return resp


@api.route('/projects/<int:project_id>', methods=['PATCH'])
@use_kwargs({
        'current_task_id': fields.Int(required=True)
    },
    locations=Location.json)
def update_project(project_id, current_task_id):
    """
    ---
    patch:
        description: Update project

        parameters:
            - name: current_task_id
              description: Task ID.
              in: body
              required: true
              type: integer

        responses:
            200:
                description: Updated Project
                schema: ProjectSchema
    """
    project = Project.query.get(project_id)
    current_task = Task.query.get(current_task_id)

    project_service.set_current_task_and_delete_workflow_data(project, current_task)

    return get_project(project_id)


@api.route('/projects/<int:project_id>/branches/<int:branch_id>', methods=['GET'])
@api.route('/projects/<int:project_id>/branches', methods=['GET'])
@login_required
@use_kwargs({
        'cluster': fields.Int(required=True),
        'num_bands': fields.Int(required=True),
    },
    locations=Location.query)
def get_branches(cluster, num_bands, project_id, branch_id=None):
    """
    ---
    get:
        description: Get project including branches with skus, metrics and decisions.

        parameters:
            - name: project_id
              description: ID of the project.
              in: path
              required: true
              type: integer
            - name: cluster
              description: ID of the cluster you want the results filtered by.
              in: query
              required: true
              type: integer
            - name: num_bands
              description: Number of bands to split the metrics into.
              in: query
              required: true
              type: integer

        responses:
            200:
                description: Returns a map of branches with the branch ID as the key. Note that "branch_id" is an
                    int not a string (Swagger 2.0 limitation).
                schema:
                    properties:
                        branch_id:
                            $ref: BranchSchema
    """

    assigned_space_break_alias = db.aliased(SpaceBreak)
    recommended_space_break_alias = db.aliased(SpaceBreak)

    query = (
        db.session.query(Branch)
            .join(BranchSku)
            .join(SkuWithBands,
                  SkuWithBands.id == BranchSku.sku_id)
            .join(Project,
                  Project.id == project_id)
            .join(Cluster,
                  Cluster.clustering_id == Project.clustering_id)
            .outerjoin(QualityFrameworkClassification, QualityFrameworkClassification.id == Branch.strategic_quality_framework_id)
            .outerjoin(SubBrand,
                       SubBrand.id == SkuWithBands.sub_brand_id)
            .outerjoin(PlanogramSummary,
                       db.and_(
                           PlanogramSummary.sku_id == SkuWithBands.id,
                           PlanogramSummary.cluster_id == Cluster.id))
            .outerjoin(BranchSkuMetricsWithBands,
                       db.and_(
                           BranchSku.id == BranchSkuMetricsWithBands.branch_sku_id,
                           BranchSkuMetricsWithBands.cluster_id == Cluster.id))
            .outerjoin(ProjectSkuDecision,
                       db.and_(
                           BranchSku.id == ProjectSkuDecision.branch_sku_id,
                           ProjectSkuDecision.project_id == Project.id,
                           ProjectSkuDecision.cluster_id == Cluster.id))
            .outerjoin(assigned_space_break_alias,
                       ProjectSkuDecision.assigned_starting_bay_id == assigned_space_break_alias.id)
            .outerjoin(recommended_space_break_alias,
                       ProjectSkuDecision.recommended_starting_bay_id == recommended_space_break_alias.id)
            .options(db.contains_eager(Branch.strategic_quality_framework))
            .options(db.contains_eager(Branch.skus).contains_eager(BranchSku.sku_with_bands))
            .options(db.contains_eager(Branch.skus).contains_eager(BranchSku.sku_with_bands)
                     .contains_eager(SkuWithBands.sub_brand))
            .options(db.contains_eager(Branch.skus).contains_eager(BranchSku.sku_with_bands)
                     .contains_eager(SkuWithBands.planogram).load_only('store_count', 'space_breaks'))
            .options(db.contains_eager(Branch.skus).contains_eager(BranchSku.metrics))
            .options(db.contains_eager(Branch.skus).contains_eager(BranchSku.decisions))
            .options(db.contains_eager(Branch.skus).contains_eager(BranchSku.decisions)
                     .contains_eager(ProjectSkuDecision.recommended_starting_bay,
                                     alias=recommended_space_break_alias).load_only('space_break'))
            .options(db.contains_eager(Branch.skus).contains_eager(BranchSku.decisions)
                     .contains_eager(ProjectSkuDecision.assigned_starting_bay,
                                     alias=assigned_space_break_alias).load_only('space_break'))
            .filter(Branch.cdh_id == Project.cdh_id, Cluster.id == cluster)
    )

    if branch_id:
        query = query.filter(Branch.id == branch_id)

    # Params are passed through to the SQL exps in the Models
    query = query.params(num_bands=num_bands, project_id=project_id, cluster_id=cluster)

    results = query.all()

    return jsonify(convert_result_set_to_dict_with_custom_key(results, 'id'))


@api.route('/projects/<int:project_id>/decisions/<int:decision_id>', methods=['PATCH'])
@login_required
@project_owner_required
@use_kwargs({
    'assigned_starting_bay_id': fields.Int(allow_none=True),
    'comment': fields.Str(),
    'is_active_choice': fields.Boolean(),
    },
    locations=Location.json)
def update_decision(assigned_starting_bay_id, comment, is_active_choice, project_id, decision_id):
    """
    ---
    patch:
        description: Record the ranging decision (i.e. starting bay) and comment.

        parameters:
            - name: project_id
              description: Project ID.
              in: path
              required: true
              type: integer
            - name: decision_id
              description: Decision ID.
              in: path
              required: true
              type: integer
            - name: assigned_starting_bay_id
              description: Bay / Space Break ID.
              in: body
              required: true
              type: integer
            - name: comment
              description: Comment.
              in: body
              required: true
              type: string
            - name: is_active_choice
              description: Flag to indicate that specific choice was made (normally set).
              in: body
              required: true
              type: boolean

        responses:
            200:
                description: Updated ProjectSkuDecision
                schema: ProjectSkuDecisionSchema
    """
    decision = db.session.query(ProjectSkuDecision)\
        .filter(ProjectSkuDecision.id == decision_id, ProjectSkuDecision.project_id == project_id).first()

    if decision is None:
        return not_found()

    if assigned_starting_bay_id != missing:
        decision.assigned_starting_bay_id = assigned_starting_bay_id
    if comment != missing:
        decision.comment = comment
    if is_active_choice != missing:
        decision.is_active_choice = is_active_choice
    db.session.commit()
    return get_one(db.session.query(ProjectSkuDecision).filter(ProjectSkuDecision.id == decision_id),
                   ProjectSkuDecisionSchema, exclude=['assigned_starting_bay', 'recommended_starting_bay'])


@api.route('/projects', methods=['POST'])
@login_required
@use_kwargs({
    'name': fields.Str(required=True),
    'section_id': fields.Int(required=True),
    'clustering_dataset_id': fields.Str(required=True),
    'metric_calculation_date_from': fields.Str(required=True),  # Ideally should be Date field but input is not ISO8601
    'metric_calculation_date_to': fields.Str(required=True),
    },
    locations=Location.json)
def add_project(name, section_id, clustering_dataset_id, metric_calculation_date_from, metric_calculation_date_to):
    """
    ---
    post:
        description: Create a project

        parameters:
            - name: name
              description: Name of the project
              in: body
              type: string
            - name: section_id
              description: ID of the section the project is for
              in: body
              type: integer
            - name: clustering_dataset_id
              description: Dataset ID of the clustering to use
              in: body
              type: string
            - name: metric_calculation_date_from
              description: From date to use for the metric calculations
              in: body
              type: string
              format: date
            - name: metric_calculation_date_to
              description: To date to use for the metric calculations
              in: body
              type: string
              format: date

        responses:
            200:
                description: Created project
                schema: ProjectSchema
    """
    try:
        project = services.project_service.add_project(
            name,
            section_id,
            clustering_dataset_id,
            datetime.strptime(metric_calculation_date_from, '%d/%m/%Y'),
            datetime.strptime(metric_calculation_date_to, '%d/%m/%Y'),
            g.current_user.id
        )
        return get_project(project.id)
    except Exception as e:
        return bad_request(e.args[0])


@api.route('/projects/<int:project_id>/clone', methods=['POST'])
@login_required
@use_kwargs({
    'name': fields.Str(required=True),
    },
    locations=Location.json)
def clone_project(name, project_id):
    """
    ---
    post:
        description: Create a new project by cloning an existing one.

        parameters:
            - name: project_id
              description: ID of project to clone from.
              in: path
              required: true
              type: integer
            - name: name
              description: Name of new project.
              in: body
              type: string

        responses:
            200:
                description: Created project
                schema: ProjectSchema

    """
    project = services.project_service.clone_project(project_id, g.current_user.id, name)
    return get_one(db.session.query(Project).filter(Project.id == project.id), ProjectSchema,
                   exclude = ['cdh', 'decisions', 'owner_user'])


@api.route('/projects/<int:project_id>/cdh_tree', methods=['GET'])
@login_required
def get_cdh_tree(project_id):
    """
    ---
    get:
        description: Return a list of items, each item a root CDH node with child nodes down to Sku level.

        parameters:
            - name: project_id
              description: Project ID.
              in: path
              required: true
              type: integer

        responses:
            200:
                description: List of CDH nodes.
                schema:
                    type: array
                    items: CdhTreeSchema
    """

    nodes = CdhTree.query.params(project_id=project_id).all()

    top_level_nodes = [node for node in nodes if node.parent_node_type is None]
    dump = CdhTreeSchema().dump(top_level_nodes, many=True)
    json = jsonify({ 'items': dump.data } )
    return json
