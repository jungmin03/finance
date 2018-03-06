"""A collection of data import functions."""
import csv
import io

from sqlalchemy.exc import IntegrityError

from finance import log
from finance.models import Account, Asset, AssetValue, db, Granularity
from finance.providers import Miraeasset
from finance.utils import DictReader


# NOTE: A verb 'import' means local structured data -> database
def import_stock_values(fin: io.TextIOWrapper, code: str):
    """Import stock values."""
    asset = Asset.get_by_symbol(code)
    reader = csv.reader(fin, delimiter=',', quotechar='"')
    # for date, open_, high, low, close_, volume, adj_close in reader:
    for date, open_, high, low, close_, volume in reader:
        try:
            AssetValue.create(
                evaluated_at=date, granularity=Granularity.day, asset=asset,
                open=open_, high=high, low=low, close=close_, volume=volume)
        except IntegrityError:
            log.warn('AssetValue for {0} on {1} already exist', code, date)
            db.session.rollback()

def import_miraeasset_foreign_records(
    fin: io.TextIOWrapper,
    account: Account,
):
    provider = Miraeasset()

    # FIXME: Get an asset object
    asset_usd = None

    for r in provider.parse_foreign_transactions(fin):
        if r.category == '해외주매수':
            # FIXME: Make this work
            asset = Asset.get_by_isin(r.code)

            with Transaction.create() as t:
                Record.create(
                    account_id=account.id,
                    asset_id=asset_usd.id,
                    transaction=t,
                    type=RecordType.withdraw,
                    created_at=r.created_at,
                    category='',
                    quantity=r.amount,
                )
                Record.create(
                    account_id=account.id,
                    asset_id=asset.id,
                    transaction=t,
                    type=RecordType.deposit,
                    created_at=r.created_at,
                    category='',
                    quantity=r.quantity,
                )
        elif r.category == '해외주매도':
            pass
        elif r.category == '해외주배당금':
            pass
    # account_id = db.Column(db.BigInteger, db.ForeignKey('account.id'))
    # asset_id = db.Column(db.BigInteger, db.ForeignKey('asset.id'))
    # transaction_id = db.Column(db.BigInteger, db.ForeignKey('transaction.id'))
    # type = db.Column(db.Enum(*record_types, name='record_type'))
    # created_at = db.Column(db.DateTime(timezone=False))
    # category = db.Column(db.String)
    # quantity = db.Column(db.Numeric(precision=20, scale=4))
