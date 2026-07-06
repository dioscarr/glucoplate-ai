from app.services.cart_store_service import CartStoreService


def test_cart_create_and_update(tmp_path):
    svc = CartStoreService()
    cart = {'title': 'test', 'items': []}
    created = svc.create(cart)
    assert 'id' in created
    cid = created['id']
    fetched = svc.get(cid)
    assert fetched['id'] == cid
    svc.update(cid, {'title': 'updated', 'items': [{'product': 'x'}]})
    updated = svc.get(cid)
    assert updated['title'] == 'updated'
    assert len(updated['items']) == 1
