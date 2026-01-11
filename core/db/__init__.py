from core.db.orm import ORM

class DB(ORM):
    def __init__(self, **options):
        try:
            ORM.__init__(self, options['engine'], pool_recycle=900, pool_size=options.get('pool_size', 5), max_overflow=-1, isolation_level="READ COMMITTED")
        except Exception as exc:
            print ("BSORM init failed: {}".format(exc))
            raise

    def try_commit(self):   
        try:
            self.commit()
        except Exception as exc:
            self.rollback()
            return False
        return True
