# encoding: utf-8
from contextlib import contextmanager
from Autodesk.Revit.DB import Transaction, TransactionGroup


@contextmanager
def revit_transaction(doc, description):
    """Safely manage Revit transactions."""
    if doc is None:
        raise AttributeError("Document is null. Transaction cannot be started.")
    tx = Transaction(doc, description)
    tx.Start()
    try:
        yield
        if tx.HasStarted():
            tx.Commit()
    except Exception as e:
        if tx.HasStarted():
            tx.RollBack()
        print("Transaction {} failed: {}".format(description,e))
        raise
    
@contextmanager
def revit_groupTransaction(doc, description):
    tg = TransactionGroup(doc, description)
    try:
        tg.Start()
        yield tg
        tg.Assimilate()
    except Exception as e:
        print("Transaction {} failed: {}".format(description,e))
        if tg.HasStarted():
            tg.RollBack()
        raise

@contextmanager
def try_and_except(description):
    try:
        yield
    except Exception as e:
        print("Operation {} failed: {}".format(description,e))
        raise