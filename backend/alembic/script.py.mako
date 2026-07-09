# revision identifiers, used by Alembic.
revision = '{{ revision }}'
down_revision = {{ down_revision | default('None') }}
branch_labels = {{ branch_labels | default('None') }}
depends_on = {{ depends_on | default('None') }}

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

{{ imports }}

def upgrade() -> None:
    {{ upgrade_ops }}

def downgrade() -> None:
    {{ downgrade_ops }}