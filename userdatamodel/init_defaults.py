from user import IdentityProvider
IDENTITY_PROVIDERS = ['google', 'itrust']

def init_defaults(db):
	with db.session as s:
		for provider in IDENTITY_PROVIDERS:
			if not (
					s.query(IdentityProvider)
					.filter(IdentityProvider.name==provider)
					.first()):
				provider = IdentityProvider(name=provider)
