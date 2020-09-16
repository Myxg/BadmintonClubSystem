#coding: utf-8

from models import DocLink

class DocLinkOpt(object):
    def __init__(self, module_id, path):
        self.path = path
        self.module_id = module_id
        self.doc_link = DocLink.objects.filter(
            module_id = self.module_id,
            path = self.path
        ).first()

    @property
    def is_linked(self):
        return True if self.doc_link else False

    @property
    def is_user_linked(self, request):
        if request.user.username == 'admin':
            return True

    def save(self):
        if self.is_linked:
            self.doc_link.save()

    def rename(self, new_path):
        if self.is_linked:
            self.doc_link.path = new_path
            self.path = new_path
            self.save()

    def delete(self):
        if self.is_linked:
            self.doc_link.delete()
