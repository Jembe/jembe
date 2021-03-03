"""
Creates Project/Tasks application component by component
with JUST MAKE IT WORK mindset. 
"""
from functools import cached_property

from jembe.component_config import CConfigRedisplayFlag, ComponentConfig
from jembe.common import ComponentRef
from jembe.utils import run_only_once
from typing import (
    Callable,
    Iterable,
    Optional,
    Sequence,
    Set,
    TYPE_CHECKING,
    Tuple,
    Type,
    Union,
    Any,
    Dict,
)
from uuid import uuid4
from math import ceil
from dataclasses import dataclass, field
from jembe import Component, action, component, config, listener, BadRequest
from sqlalchemy.exc import SQLAlchemyError
from wtforms_sqlalchemy.orm import model_form
from dapp.models import Project, Task
from dapp.jmb import jmb
from dapp.db import db

if TYPE_CHECKING:
    from flask_sqlalchemy.model import Model
    from flask import Response
    from wtforms import Form
    from jembe import Event

ProjectForm = model_form(Project, db, exclude=("tasks",))
TaskForm = model_form(Task, db, exclude=("project",))


@dataclass
class Confirmation:
    title: str
    question: str
    action: str
    params: dict = field(default_factory=dict)


@config(Component.Config(changes_url=False, template="common/confirmation.html"))
class ConfirmationDialog(Component):
    def __init__(
        self, confirmation: Optional[Confirmation] = None, source: Optional[str] = None
    ) -> None:
        super().__init__()

    @classmethod
    def load_init_param(cls, name: str, value: Any) -> Any:
        if name == "confirmation":
            return (
                Confirmation(
                    title=value.get("title"),
                    question=value.get("question"),
                    action=value.get("action"),
                    params=value.get("params"),
                )
                if value is not None
                else None
            )
        return super().load_init_param(name, value)

    @listener(event="requestConfirmation")
    def on_request_confirmation(self, event: "Event"):
        self.state.confirmation = event.confirmation
        self.state.source = event.source_exec_name

    @action
    def choose(self, choice: str):
        self.emit(
            "confirmation",
            choice=choice,
            action=self.state.confirmation.action,
            action_params=self.state.confirmation.params,
        ).to(self.state.source)
        self.state.confirmation = None
        self.state.source = None


@dataclass
class Notification:
    message: str
    level: str = "info"


@config(Component.Config(changes_url=False, template="common/notifications.html"))
class Notifications(Component):
    def __init__(self, notifications: Optional[Dict[str, Notification]] = None) -> None:
        if notifications is not None:
            # remove notifications id where notification[id] == None
            self.state.notifications = {
                id: n for id, n in notifications.items() if n is not None
            }
        else:
            self.state.notifications = dict()

        super().__init__()

    @listener(event="pushNotification")
    def on_push_notification(self, event):
        self.state.notifications[str(uuid4())] = event.params.get(
            "notification", Notification("Undefined message")
        )


# lib
#######


class FormLoadDumpMixin:
    @classmethod
    def dump_init_param(cls, name: str, value: Any) -> Any:
        if name == "form":
            return value.data if value is not None else dict()
        return super().dump_init_param(name, value)  # type:ignore

    @classmethod
    def load_init_param(cls, name: str, value: Any) -> Any:
        if name == "form":
            return ProjectForm(data=value)
        return super().load_init_param(name, value)  # type:ignore


class OnConfirmationSupportMixin:
    @listener(event="confirmation")
    def on_confirmation(self, event: "Event"):
        if hasattr(self, event.action) and event.choice == "ok":
            return getattr(self, event.action)(**event.action_params)


class ViewRecord(OnConfirmationSupportMixin, Component):
    class Config(Component.Config):
        TEMPLATES = dict(default="common/view.html", inline="common/view_inline.html")

        def __init__(
            self,
            model: Type["Model"],
            template: Optional[Union[str, Iterable[str]]] = None,
            components: Optional[Dict[str, ComponentRef]] = None,
            inject_into_components: Optional[
                Callable[["Component", "ComponentConfig"], dict]
            ] = None,
            redisplay: Tuple["CConfigRedisplayFlag", ...] = (),
            changes_url: bool = True,
            url_query_params: Optional[Dict[str, str]] = None,
        ):
            self.model = model
            if template is None:
                template = (self.default_template_name, self.TEMPLATES["default"])

            super().__init__(
                template=template,
                components=components,
                inject_into_components=inject_into_components,
                redisplay=redisplay,
                changes_url=changes_url,
                url_query_params=url_query_params,
            )

    _config: Config

    def __init__(self, record_id: int, _record: Optional["Model"] = None) -> None:
        self._record = _record
        super().__init__()

    @property
    def record(self) -> "Model":
        if self._record is None or self._record.id != self.state.record_id:
            self._record = self._config.model.query.get(self.state.record_id)
        return self._record

    @action
    def delete_record(self, confirmed: bool = False) -> Optional[bool]:
        if not confirmed:
            # display confirmation dialog
            self.emit(
                "requestConfirmation",
                confirmation=Confirmation(
                    title="Delete {}".format(self.record),
                    question="Are you sure?",
                    action="delete_record",
                    params=dict(confirmed=True),
                ),
            )
        else:
            # delete record
            db.session.delete(self.record)
            db.session.commit()
            self.emit(
                "pushNotification",
                notification=Notification("{} deleted.".format(self.record)),
            )
            self.emit("delete", record_id=self.record.id, record=self.record)
            return False
        return None


class EditRecord(FormLoadDumpMixin, OnConfirmationSupportMixin, Component):
    class Config(Component.Config):
        TEMPLATES = dict(default="common/edit.html", inline="common/edit_inline.html")

        def __init__(
            self,
            model: Type["Model"],
            form: Type["Form"],
            ask_for_prev_next_record: bool = False,
            template: Optional[Union[str, Iterable[str]]] = None,
            components: Optional[Dict[str, ComponentRef]] = None,
            inject_into_components: Optional[
                Callable[["Component", "ComponentConfig"], dict]
            ] = None,
            redisplay: Tuple["CConfigRedisplayFlag", ...] = (),
            changes_url: bool = True,
            url_query_params: Optional[Dict[str, str]] = None,
        ):
            self.model = model
            self.form = form
            self.ask_for_prev_next_record = ask_for_prev_next_record
            if template is None:
                template = (self.default_template_name, self.TEMPLATES["default"])
            super().__init__(
                template=template,
                components=components,
                inject_into_components=inject_into_components,
                redisplay=redisplay,
                changes_url=changes_url,
                url_query_params=url_query_params,
            )

    _config: Config

    def __init__(
        self,
        record_id: int,
        form: Optional["Form"] = None,
        prev_record_id: Optional[int] = None,
        next_record_id: Optional[int] = None,
        _record: Optional["Model"] = None,
    ):
        self._record = _record
        super().__init__()

    @run_only_once(for_state="record_id")
    def mount(self):
        if self._record is not None:
            self.record = self._record
        else:
            self.record = self._config.model.query.get(self.state.record_id)

        if self.state.form is None:
            self.state.form = self._config.form(obj=self.record)

        if (
            self._config.ask_for_prev_next_record
            and self.state.prev_record_id is None
            and self.state.next_record_id is None
        ):
            self.emit(
                "askQuestion", question="getPrevNext", record_id=self.state.record_id
            ).to("/**/.")

    @action
    def save(self):
        self.mount()
        if self.state.form.validate():
            try:
                self.state.form.populate_obj(self.record)
                db.session.commit()
                self.emit("save", record=self.record, record_id=self.record.id)
                self.emit(
                    "pushNotification",
                    notification=Notification("{} saved.".format(str(self.record))),
                )
                # don't execute display
                # parent should listen for save and decite what to do
                return False
            except SQLAlchemyError as sql_error:
                self.emit(
                    "pushNotification",
                    notification=Notification(
                        str(getattr(sql_error, "orig", sql_error)), "error"
                    ),
                )
                return True
        # form is invalid redislay compoent and show errors
        # if the state is changed
        return None

    @action
    def cancel(self, confirmed=False):
        if self._is_record_modified() and not confirmed:
            self.emit(
                "requestConfirmation",
                confirmation=Confirmation(
                    title="Cancel Edit",
                    question="Are you sure, all changes will be lost?",
                    action="cancel",
                    params=dict(confirmed=True),
                ),
            )
        else:
            self.emit("cancel")
            # don't execute display even if the state has changed
            return False

    @action
    def goto_record(self, record_id: int, confirmed=False):
        if self._is_record_modified() and not confirmed:
            self.emit(
                "requestConfirmation",
                confirmation=Confirmation(
                    title="Moving to",
                    question="Are you sure, all changes will be lost?",
                    action="goto",
                    params=dict(record_id=record_id, confirmed=True),
                ),
            )
        else:
            # display edit with other record
            self.state.record_id = record_id
            self.state.form = None
            self.state.prev_record_id = None
            self.state.next_record_id = None
            self.mount()
        return True

    def display(self) -> Union[str, "Response"]:
        self.mount()
        self.model_info = getattr(self._config.model, "__table_args__", dict()).get(
            "info", dict()
        )
        return super().display()

    @listener(event="answerQuestion", source="/**/.")
    def on_answer_question(self, answer: "Event"):
        if answer.question == "getPrevNext":
            self.state.prev_record_id = answer.prev_record_id
            self.state.next_record_id = answer.next_record_id

    @listener(event="redisplay")
    def on_redisplay(self, event: "Event"):
        return True

    def _is_record_modified(self) -> bool:
        self.mount()
        db.session.begin_nested()
        self.state.form.populate_obj(self.record)
        is_modified = db.session.is_modified(self.record)
        db.session.rollback()
        return is_modified


class AddRecord(FormLoadDumpMixin, OnConfirmationSupportMixin, Component):
    class Config(Component.Config):
        TEMPLATES = dict(default="common/add.html", inline="common/add_inline.html")
        BASE_TEMPLATE = None

        def __init__(
            self,
            model: Type["Model"],
            form: Type["Form"],
            parent_id_field_name: Optional[str] = None,
            template: Optional[Union[str, Iterable[str]]] = None,
            components: Optional[Dict[str, ComponentRef]] = None,
            inject_into_components: Optional[
                Callable[["Component", "ComponentConfig"], dict]
            ] = None,
            redisplay: Tuple["CConfigRedisplayFlag", ...] = (),
            changes_url: bool = True,
            url_query_params: Optional[Dict[str, str]] = None,
        ):
            self.model = model
            self.form = form
            self.parent_id_field_name = parent_id_field_name
            if template is None:
                template = (self.default_template_name, self.TEMPLATES["default"])
            super().__init__(
                template=template,
                components=components,
                inject_into_components=inject_into_components,
                redisplay=redisplay,
                changes_url=changes_url,
                url_query_params=url_query_params,
            )

    _config: Config

    def __init__(
        self, form: Optional["Form"] = None, parent_id: Optional[int] = None
    ) -> None:
        super().__init__()

    def get_new_record(self) -> "Model":
        if self._config.parent_id_field_name is None:
            return self._config.model()
        else:
            return self._config.model(
                **{self._config.parent_id_field_name: self.state.parent_id}
            )

    @run_only_once
    def mount(self):
        if self.state.form is None:
            self.state.form = self._config.form(obj=self.get_new_record())

    @action
    def save(self) -> Optional[bool]:
        self.mount()
        if self.state.form.validate():
            try:
                record = self.get_new_record()
                self.state.form.populate_obj(record)
                db.session.add(record)
                db.session.commit()
                self.emit("save", record=record, record_id=record.id)
                self.emit(
                    "pushNotification",
                    notification=Notification("{} saved".format(str(record))),
                )
                # don't execute display
                return False
            except SQLAlchemyError as sql_error:
                self.emit(
                    "pushNotification",
                    notification=Notification(
                        str(getattr(sql_error, "orig", sql_error)), "error"
                    ),
                )
                return True
        return None

    @action
    def cancel(self, confirmed=False):
        if self._is_record_modified() and not confirmed:
            self.emit(
                "requestConfirmation",
                confirmation=Confirmation(
                    title="Cancel Add",
                    question="Are you sure, all changes will be lost?",
                    action="cancel",
                    params=dict(confirmed=True),
                ),
            )
        else:
            self.emit("cancel")
            return False

    def display(self) -> Union[str, "Response"]:
        self.mount()
        self.model_info = getattr(self._config.model, "__table_args__", dict()).get(
            "info", dict()
        )
        return super().display()

    def _is_record_modified(self) -> bool:
        self.mount()
        new_record = self.get_new_record()
        self.state.form.populate_obj(new_record)
        empty_record = self.get_new_record()
        for column_name in new_record.__table__.columns.keys():
            if getattr(new_record, column_name) != getattr(empty_record, column_name):
                return True
        return False


class ListRecords(OnConfirmationSupportMixin, Component):
    class Config(Component.Config):
        TEMPLATES: Dict[str, str] = dict()
        BASE_TEMPLATE = "common/list_records.html"

        def __init__(
            self,
            model: Type["Model"],
            columns: Optional[Sequence[str]] = None,
            parent_id_field_name: Optional[str] = None,
            template: Optional[Union[str, Iterable[str]]] = None,
            components: Optional[Dict[str, ComponentRef]] = None,
            inject_into_components: Optional[
                Callable[["Component", "ComponentConfig"], dict]
            ] = None,
            redisplay: Tuple["CConfigRedisplayFlag", ...] = (),
            changes_url: bool = True,
            url_query_params: Optional[Dict[str, str]] = None,
        ):
            self.model = model
            self.parent_id_field_name = parent_id_field_name
            if columns:
                self.columns = [c for c in model.__table__.columns if c.name in columns]
            else:
                self.columns = [
                    c
                    for c in model.__table__.columns
                    if c.name not in ("id", self.parent_id_field_name)
                ]
            if url_query_params is None:
                url_query_params = dict(p="page", ps="page_size")

            if template is None:
                template = ("", self.BASE_TEMPLATE)

            super().__init__(
                template=template,
                components=components,
                inject_into_components=inject_into_components,
                redisplay=redisplay,
                changes_url=changes_url,
                url_query_params=url_query_params,
            )

    _config: Config

    def __init__(
        self, parent_id: Optional[int] = None, page: int = 0, page_size: int = 5
    ):
        super().__init__()

    @action
    def delete_record(self, record_id: int, confirmed: bool = False) -> Optional[bool]:
        if not confirmed:
            # display confirmation dialog
            self.emit(
                "requestConfirmation",
                confirmation=Confirmation(
                    title="Delete {}".format(self._config.model.query.get(record_id)),
                    question="Are you sure?",
                    action="delete_record",
                    params=dict(record_id=record_id, confirmed=True),
                ),
            )
        else:
            # delete record
            record = self._config.model.query.get(record_id)
            db.session.delete(record)
            db.session.commit()
            self.emit(
                "pushNotification",
                notification=Notification("{} deleted.".format(record)),
            )
            # redisplay list when record is deleted
            return True
        return None

    def display(self) -> Union[str, "Response"]:
        Record = self._config.model
        records = Record.query
        if (
            self.state.parent_id is not None
            and self._config.parent_id_field_name is not None
        ):
            records = records.filter_by(
                **{self._config.parent_id_field_name: self.state.parent_id}
            )

        self.records_count = records.count()
        self.total_pages = ceil(self.records_count / self.state.page_size)
        if self.state.page < 1:
            self.state.page = 1
        if self.state.page >= self.total_pages:
            self.state.page = self.total_pages
        start = (self.state.page - 1) * self.state.page_size
        self.records = records.order_by(Record.id.desc())[
            start : start + self.state.page_size
        ]

        self.model_info = getattr(self._config.model, "__table_args__", dict()).get(
            "info", dict()
        )
        return super().display()

    @listener(event="askQuestion", source="./**")
    def on_question_asked(self, event: "Event"):
        if event.question == "getPrevNext":
            prev_record_id, next_record_id = self.get_prev_next_id(event.record_id)
            self.emit(
                "answerQuestion",
                question=event.question,
                record_id=event.record_id,
                prev_record_id=prev_record_id,
                next_record_id=next_record_id,
            ).to(event.source_full_name)
        return False

    def get_prev_next_id(self, record_id) -> Tuple[Optional[int], Optional[int]]:
        # TODO make abstraction of this query manipulation to get next, previous when
        # order is by any other field or when additional filters are applied
        Record = self._config.model
        prev = (
            Record.query.with_entities(Record.id)
            .order_by(Record.id)
            .filter(Record.id > record_id)
            .first()
        )
        next = (
            Record.query.with_entities(Record.id)
            .order_by(Record.id.desc())
            .filter(Record.id < record_id)
            .first()
        )
        return (
            prev[0] if prev is not None else None,
            next[0] if next is not None else None,
        )


class ListRecordsInline(ListRecords):
    class Config(ListRecords.Config):
        BASE_TEMPLATE = "common/list_records_inline.html"

    def __init__(
        self,
        display_mode: Optional[str] = None,
        editing_records: Set[int] = set(),
        parent_id: Optional[int] = None,
        page: int = 0,
        page_size: int = 5,
    ):
        if display_mode not in (None, "add"):
            self.state.display_mode = None
        super().__init__(parent_id=parent_id, page=page, page_size=page_size)

    @listener(event="delete", source=["./view.*"])
    def on_child_deleted(self, event: "Event"):
        # redisplay list
        return True

    @listener(event="_display", source=["./add"])
    def on_add_display(self, event: "Event"):
        if self.state.display_mode != event.source_name:
            # when adding go to first page
            # but allow navigation afterward
            self.state.page = 1
        self.state.display_mode = event.source_name

    @listener(event="_display", source=["./edit.*"])
    def on_edit_display(self, event: "Event"):
        if event.source:
            # chech why event.source is necessary
            # if it's necessary make if statement readable and obouse to
            # someone who dont know the jembe
            self.state.editing_records.add(event.source.state.record_id)

    @listener(event="cancel", source=["./add"])
    def on_add_cancel(self, event: "Event"):
        self.state.display_mode = None

    @listener(event="save", source=["./add"])
    def on_add_save(self, event: "Event"):
        self.state.display_mode = None

    @listener(event=["save", "cancel"], source=["./edit.*"])
    def on_edit_finish(self, event: "Event"):
        if event.source:
            self.state.editing_records.remove(event.source.state.record_id)


class ListRecordsSwap(ListRecords):
    class Config(ListRecords.Config):
        BASE_TEMPLATE = "common/list_records_swap.html"

    def __init__(
        self,
        display_mode: Optional[str] = None,
        parent_id: Optional[int] = None,
        page: int = 0,
        page_size: int = 5,
    ):
        if display_mode not in (None, "edit", "add"):
            raise BadRequest()
        self.edit_record_id = None
        super().__init__(parent_id=parent_id, page=page, page_size=page_size)

    @listener(event="_display", source=["./edit", "./add"])
    def on_child_display(self, event: "Event"):
        self.state.display_mode = event.source_name

    @listener(event="cancel", source=["./edit", "./add"])
    def on_child_cancel(self, event: "Event"):
        self.state.display_mode = None

    @listener(event="save", source=["./add"])
    def on_add_successful(self, event: "Event"):
        self.state.display_mode = "edit"
        self.edit_record_id = event.params["record_id"]

    @listener(event="save", source=["./edit"])
    def on_edit_successful(self, event: "Event"):
        # TODO force edit to redisplay itself on save
        self.emit("redisplay").to("./edit")

    def display(self) -> Union[str, "Response"]:
        if self.state.display_mode is None:
            # if mode is display projects table
            return super().display()
        return self.render_template()


# Projects
##########
# TODO add dommorph
# TODO add browser states to component
# TODO display generic error dialog when error is hapend in x-jembe request
# TODO add task mark completed
# TODO add more fields to project and task
# TODO make it looks nice
# TODO add remove polyfil in js (??)
# TODO add jmb-on.keydown/keyup.enter.esc etc mofifiers
# TODO use regular if else for readability in examples
# TODO extensive comment all python code that is not understud to someone who does know python
# TODO make course that will be created to build this version step by step
# TODO When going back with browser execute confirmation if needed --for next version
# generate system event _browser_navigation
# TODO create API for calling other copmponenet actions like ---- no need for this you can always add listeners if needed
# self.emit("callAction", action="acton_name", params=dict()).to("exec_name")
# self.emit("callDisplay", force=True|False).to("..")
@jmb.page(
    "main",
    Component.Config(
        components=dict(
            projects=(
                ListRecordsSwap,
                ListRecordsSwap.Config(
                    model=Project,
                    components=dict(
                        edit=(
                            EditRecord,
                            EditRecord.Config(
                                model=Project,
                                form=ProjectForm,
                                ask_for_prev_next_record=True,
                                components=dict(
                                    tasks=(
                                        ListRecordsInline,
                                        ListRecordsInline.Config(
                                            model=Task,
                                            parent_id_field_name="project_id",
                                            components=dict(
                                                view=(
                                                    ViewRecord,
                                                    ViewRecord.Config(
                                                        model=Task,
                                                        template=ViewRecord.Config.TEMPLATES[
                                                            "inline"
                                                        ],
                                                        changes_url=False,
                                                    ),
                                                ),
                                                add=(
                                                    AddRecord,
                                                    AddRecord.Config(
                                                        model=Task,
                                                        form=TaskForm,
                                                        parent_id_field_name="project_id",
                                                        template=AddRecord.Config.TEMPLATES[
                                                            "inline"
                                                        ],
                                                        changes_url=False,
                                                    ),
                                                ),
                                                edit=(
                                                    EditRecord,
                                                    EditRecord.Config(
                                                        model=Task,
                                                        form=TaskForm,
                                                        template=EditRecord.Config.TEMPLATES[
                                                            "inline"
                                                        ],
                                                        changes_url=False,
                                                    ),
                                                ),
                                            ),
                                            inject_into_components=lambda self, _config: dict(
                                                parent_id=self.state.parent_id
                                            ),
                                        ),
                                    )
                                ),
                                inject_into_components=lambda self, _config: dict(
                                    parent_id=self.state.record_id
                                ),
                            ),
                        ),
                        add=(
                            AddRecord,
                            AddRecord.Config(model=Project, form=ProjectForm),
                        ),
                    ),
                ),
            ),
            confirmation=ConfirmationDialog,
            notifications=Notifications,
        )
    ),
)
class MainPage(Component):
    class Config(Component.Config):
        @cached_property
        def supported_display_modes(self) -> Tuple[str, ...]:
            return tuple(
                name
                for name, conf in self.components_configs.items()
                if conf.changes_url == True
            )

    _config: Config

    def __init__(self, display_mode: Optional[str] = None):
        if display_mode not in self._config.supported_display_modes:
            self.state.display_mode = self._config.supported_display_modes[0]
        super().__init__()

    @listener(event="_display", source=["./*"])
    def on_child_display(self, event: "Event"):
        if event.source_name in self._config.supported_display_modes:
            self.state.display_mode = event.source_name
