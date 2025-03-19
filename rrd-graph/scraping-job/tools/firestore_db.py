import os 
from google.cloud import datastore



class Thread:
    def __init__(self, project_id, metadata_database_id, thread_id=None, display_name=None, type=None, context=None, tasks=None, extra_instructions=None, job_ids=None, platform_ids=None, target_locations=None, sentiment_goal=None, created_at=None, updated_at=None) -> None:
        self.project_id = project_id
        self.metadata_database_id = metadata_database_id
        self.thread_id = thread_id
        self.display_name = display_name
        self.type = type
        self.context = context
        self.tasks = tasks
        self.extra_instructions = extra_instructions
        self.job_ids = job_ids
        self.platform_ids = platform_ids
        self.target_locations = target_locations
        self.sentiment_goal = sentiment_goal
        self.created_at = created_at
        self.updated_at = updated_at
    
    @classmethod
    def from_dict(self, source) -> 'Thread':
        thread = Thread(
            project_id=source.get('project_id'),
            metadata_database_id=source.get('metadata_database_id'),
            thread_id=source.get('thread_id'),
            display_name=source.get('display_name'),
            type=source.get('type'),
            context=source.get('context'),
            tasks=source.get('tasks'),
            extra_instructions=source.get('extra_instructions'),
            job_ids=source.get('job_ids'),
            platform_ids = source.get('platform_ids'),
            target_locations=source.get('target_locations'),
            sentiment_goal=source.get('sentiment_goal'),
            created_at=source.get('created_at'),
            updated_at=source.get('updated_at')
        )
        return thread



    def to_dict(self):
        dest = {
            'thread_id': self.thread_id,
            'display_name': self.display_name,
            'type': self.type,
            'context': self.context,
            'tasks': self.tasks,
            'extra_instructions': self.extra_instructions,
            'job_ids': self.job_ids,
            'platform_ids': self.platform_ids,
            'target_locations': self.target_locations,
            'sentiment_goal': self.sentiment_goal,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        if dest['created_at']:
            dest['created_at'] = dest['created_at'].isoformat()
        if dest['updated_at']:
            dest['updated_at'] = dest['updated_at'].isoformat()
        return dest

    def __repr__(self):
        return f"Thread(\
            thread_id={self.thread_id}, \
            display_name={self.display_name}, \
            type={self.type}, \
            context={self.context}, \
            tasks={self.tasks},\
            extra_instructions={self.extra_instructions}, \
            job_ids={self.job_ids}, \
            platform_ids = {self.platform_ids}, \
            target_locations={self.target_locations}, \
            sentiment_goal={self.sentiment_goal}, \
            created_at={self.created_at}, \
            updated_at={self.updated_at} \
        )"


    # Function to retrieve a Thread by ID
    def thread_by_id(self, thread_id):
        client = datastore.Client(project=self.project_id, database=self.metadata_database_id)
        query = client.query(kind="threads")
        # doc = db.collection(u'threads').document(thread_id)
        query.add_filter(filter=datastore.query.PropertyFilter("thread_id", "=", thread_id))
        results = list(query.fetch())
        entity = results.pop()
        if entity:
            print(f"{entity}")
            thread = Thread.from_dict(entity)
            print(thread.platform_ids)
            return thread
        else:
            print(f"No thread by id {thread_id}")
            return None

    def create_thread_entity(self):
        client = datastore.Client(project=self.project_id, database=self.metadata_database_id)
        key = client.key("threads")
        entity = datastore.Entity(key=key)
        entity.update(
           self.to_dict()
        )
        client.put(entity) 


class Job:
    def __init__(self, project_id, metadata_database_id, job_id=None, thread_id=None, platform_id=None, keywords=[], interval=5, created_at=None, updated_at=None) -> None:
        self.project_id = project_id
        self.metadata_database_id = metadata_database_id
        self.job_id = job_id
        self.thread_id = thread_id
        self.platform_id = platform_id
        self.keywords = keywords
        self.interval = interval
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    def from_dict(self, source) -> 'Job':
        job = Job(
            project_id=source.get('project_id'),
            metadata_database_id=source.get('metadata_database_id'),
            job_id=source.get('job_id'),
            thread_id=source.get('thread_id'),
            platform_id=source.get('platform_id'),
            keywords=source.get('keywords'),
            interval = source.get('interval', None),
            created_at=source.get('created_at'),
            updated_at=source.get('updated_at')
        )
        return job

    def to_dict(self):
        dest = {
            'job_id': self.job_id,
            'thread_id': self.thread_id,
            'platform_id': self.platform_id,
            'keywords': self.keywords,
            'interval': self.interval,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        if dest['created_at']:
            dest['created_at'] = dest['created_at'].isoformat()
        if dest['updated_at']:
            dest['updated_at'] = dest['updated_at'].isoformat()
        return dest

    def create_job(self):
        client = datastore.Client(project=self.project_id, database=self.metadata_database_id)
        client.put(self)

    def job_by_id(self, job_id):
        client = datastore.Client(project=self.project_id, database=self.metadata_database_id)
        query = client.query(kind="jobs")
        query.add_filter(filter=datastore.query.PropertyFilter("job_id", "=", job_id))
        results = list(query.fetch())
        entity = results.pop()
        if entity:
            print(f"{entity}")
            job = Job.from_dict(source=entity)
            print(job.job_id)
            return job
        else:
            print(f"No job by id: {job_id}")
            return None

    def create_job_entity(self):
        client = datastore.Client(project=self.project_id, database=self.metadata_database_id)
        key = client.key("jobs")
        entity = datastore.Entity(key=key)
        entity.update(
           self.to_dict()
        )
        client.put(entity) 




class Platform:
    def __init__(self, project_id, metadata_database_id, platform_id=None, display_name=None, credentials=None, endpoint=None, created_at=None, updated_at=None) -> None:
        self.project_id = project_id
        self.metadata_database_id = metadata_database_id
        self.platform_id = platform_id
        self.display_name = display_name
        self.credentials = credentials
        self.endpoint = endpoint
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    def from_dict(self, source) -> 'Platform':
        platform = Platform(
            project_id=source.get('project_id'),
            metadata_database_id=source.get('metadata_database_id'),
            platform_id=source.get('platform_id'),
            display_name=source.get('display_name'),
            credentials=source.get('credentials'),
            endpoint=source.get('endpoint'),
            created_at=source.get('created_at'),
            updated_at=source.get('updated_at')
        )
        return platform

    def to_dict(self):
        dest = {
            'platform_id': self.platform_id,
            'display_name': self.display_name,
            'credentials': self.credentials,
            'endpoint': self.endpoint,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        if dest['created_at']:
            dest['created_at'] = dest['created_at'].isoformat()
        if dest['updated_at']:
            dest['updated_at'] = dest['updated_at'].isoformat()
        return dest

    def platform_by_id(self, platform_id):
        client = datastore.Client(project=self.project_id, database=self.metadata_database_id)
        query = client.query(kind="platforms")
        print(f"platform_id: #{platform_id}#, project_id: #{self.project_id}#")
        query.add_filter(filter=datastore.query.PropertyFilter("platform_id", "=", platform_id))
        
        results = list(query.fetch())
        print(f"results: {results}")
        
        if len(results) > 0:
            entity = results.pop()
            print(f"{entity}")
            pt = Platform.from_dict(entity)
            print(pt.platform_id)
            return pt
        else:
            print(f"No platform by id: {platform_id}")
            return None

    def create_platform_entity(self):
        client = datastore.Client(project=self.project_id, database=self.metadata_database_id)
        key = client.key("platforms")
        entity = datastore.Entity(key=key)
        entity.update(
           self.to_dict()
        )
        client.put(entity)



def create_entities():

    project_id = os.getenv("PROJECT_ID") or "play-dev-ops"
    metadata_database_id = os.getenv("METADATA_DATABASE_ID") or "rrd-metadb"

    # t = Thread(project_id="play-dev-ops", metadata_database_id="rrd-metadb")
    # st = t.thread_by_id("10001")
    t = Thread(project_id=project_id, metadata_database_id=metadata_database_id)
    t.create_thread_entity()
    j = Job(project_id=project_id, metadata_database_id=metadata_database_id)
    j.create_job_entity()
    p = Platform(project_id=project_id, metadata_database_id=metadata_database_id)
    p.create_platform_entity()



# main for local test
if __name__ == "__main__":
    create_entities()




