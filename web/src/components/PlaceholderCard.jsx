import { Card, CardContent, Typography } from '@mui/material';

export default function PlaceholderCard({ title, description }) {
  return (
    <Card>
      <CardContent>
        <Typography component="h3" variant="h6">
          {title}
        </Typography>
        {description ? <Typography color="text.secondary">{description}</Typography> : null}
      </CardContent>
    </Card>
  );
}
