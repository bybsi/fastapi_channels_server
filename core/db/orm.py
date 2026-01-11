import sqlalchemy
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.orm import sessionmaker, scoped_session, class_mapper, relationship
from sqlalchemy.ext.declarative import declarative_base

Session = scoped_session(sessionmaker())

class ByBTable():
    def __init__(self, name, base, engine, session, metadata):
        self.table_class = type(name+"_table_class", (base,), {'__table__':Table(name, metadata, autoload_with=engine)})
        self.session = session

    def __getattr__(self, name):
        try:
            return getattr(self.session.query(self), name)
        except AttributeError:
            try: 
                return getattr(self.table_class, name)
            except AttributeError:
                return getattr(self.table_class.__table__, name)

    def insert(self, **kwargs):
        record = self.table_class(**kwargs)
        self.session.add(record)
        return record
    
    def relate(self, propname, tableref, **kwargs):
        class_mapper(self.table_class)._configure_property(propname, relationship(tableref.table_class, **kwargs))

    def join(self, tableref, *args, **kwargs):
        if kwargs.pop('isouter', False):
            return self.session.query(self).outerjoin(tableref.table_class, *args, **kwargs)
        else:
            return self.session.query(self).join(tableref.table_class, *args, **kwargs)

    def outerjoin(self, tableref, *args, **kwargs):
        return self.session.query(self).outerjoin(tableref.table_class, *args, **kwargs)

class ByBSession():
    def __init__(self):
        self.Session = Session

    def __getattr__(self, name):
        try:
            return getattr(self.Session(), name)
        except AttributeError:
            return getattr(self.Session, name)

    def query(self, *args):
        table_classes = [x.table_class if type(x) is ByBTable else x for x in args]
        return self.Session().query(*table_classes)

class ORM():
    def __init__(self, *args, **kwargs):
        self.engine = create_engine(*args, **kwargs)
        self.base = declarative_base()
        self.session = ByBSession()
        self.metadata = MetaData()
        if self.session.Session.registry.has():
            # Means the session is in use.
            self.session.Sessions = scoped_session(sessionmaker())
        self.session.Session.configure(bind = self.engine)
        self.engine.execute = lambda x: self.execute(x)
        self.bind = self.engine
        self.cache = {}

    def __getattr__(self, name):
        return self.entity(name)

    def entity(self, name):
        if name[:4] == 'tbl_':
            if name not in self.cache:
                self.cache[name] = ByBTable(
                    name, 
                    self.base, 
                    self.engine, 
                    self.session, 
                    self.metadata)
            return self.cache[name]
        else: 
            return getattr(self.session, name)

    def connection(self):
        return self.session._connection_for_bind(self.metadata.bind)

    def delete(self, **kwargs):
        record = self.table_class(**kwargs)
        self.session.delete(record)

    def execute(self, arg, *args, **kwargs):
        if type(arg) is str or type(arg) is bytes:
            arg = sqlalchemy.text(arg)
        return self.connection().execute(arg, *args, **kwargs)

    def join(self, table, *args, **kwargs):
        return table.join(*args, **kwargs)

